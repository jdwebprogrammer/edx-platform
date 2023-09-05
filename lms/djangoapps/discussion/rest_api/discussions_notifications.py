"""
Discussion notifications sender util.
"""
from django.conf import settings
from openedx_events.learning.data import UserNotificationData
from openedx_events.learning.signals import USER_NOTIFICATION_REQUESTED

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole
from openedx.core.djangoapps.course_groups.models import CourseCohortsSettings, CourseUserGroup
from openedx.core.djangoapps.discussions.utils import get_divided_discussions
from openedx.core.djangoapps.django_comment_common.comment_client.comment import Comment
from openedx.core.djangoapps.django_comment_common.comment_client.subscriptions import Subscription
from openedx.core.djangoapps.django_comment_common.models import (
    FORUM_ROLE_ADMINISTRATOR,
    FORUM_ROLE_COMMUNITY_TA,
    FORUM_ROLE_MODERATOR,
    CourseDiscussionSettings,
    Role
)


def send_response_notifications(thread, course, creator, parent_id=None):
    """
    Send notifications to users who are subscribed to the thread.
    """
    notification_sender = DiscussionNotificationSender(thread, course, creator, parent_id)
    notification_sender.send_new_comment_notification()
    notification_sender.send_new_response_notification()
    notification_sender.send_new_comment_on_response_notification()
    notification_sender.send_response_on_followed_post_notification()


class DiscussionNotificationSender:
    """
    Class to send notifications to users who are subscribed to the thread.
    """

    def __init__(self, thread, course, creator, parent_id=None):
        self.thread = thread
        self.course = course
        self.creator = creator
        self.parent_id = parent_id
        self.parent_response = None
        self._get_parent_response()

    def _send_notification(self, user_ids, notification_type, extra_context=None):
        """
        Send notification to users
        """
        if not user_ids:
            return

        if extra_context is None:
            extra_context = {}

        notification_data = UserNotificationData(
            user_ids=[int(user_id) for user_id in user_ids],
            context={
                "replier_name": self.creator.username,
                "post_title": self.thread.title,
                "course_name": self.course.display_name,
                **extra_context,
            },
            notification_type=notification_type,
            content_url=f"{settings.DISCUSSIONS_MICROFRONTEND_URL}/{str(self.course.id)}/posts/{self.thread.id}",
            app_name="discussion",
            course_key=self.course.id,
        )
        USER_NOTIFICATION_REQUESTED.send_event(notification_data=notification_data)

    def _get_parent_response(self):
        """
        Get parent response object
        """
        if self.parent_id and not self.parent_response:
            self.parent_response = Comment(id=self.parent_id).retrieve()

        return self.parent_response

    def send_new_response_notification(self):
        """
        Send notification to users who are subscribed to the main thread/post i.e.
        there is a response to the main thread.
        """
        if not self.parent_id and self.creator.id != int(self.thread.user_id):
            self._send_notification([self.thread.user_id], "new_response")

    def _response_and_thread_has_same_creator(self) -> bool:
        """
        Check if response and main thread have same author.
        """
        return int(self.parent_response.user_id) == int(self.thread.user_id)

    def send_new_comment_notification(self):
        """
        Send notification to parent thread creator i.e. comment on the response.
        """
        #
        if (
            self.parent_response and
            self.creator.id != int(self.thread.user_id)
        ):
            # use your if author of response is same as author of post.
            author_name = "your" if self._response_and_thread_has_same_creator() else self.parent_response.username
            context = {
                "author_name": author_name,
            }
            self._send_notification([self.thread.user_id], "new_comment", extra_context=context)

    def send_new_comment_on_response_notification(self):
        """
        Send notification to parent response creator i.e. comment on the response.
        Do not send notification if author of response is same as author of post.
        """
        if (
            self.parent_response and
            self.creator.id != int(self.parent_response.user_id) and not
            self._response_and_thread_has_same_creator()
        ):
            self._send_notification([self.parent_response.user_id], "new_comment_on_response")

    def _check_if_subscriber_is_not_thread_or_content_creator(self, subscriber_id) -> bool:
        """
        Check if the subscriber is not the thread creator or response creator
        """
        return (
            subscriber_id != int(self.thread.user_id) and
            subscriber_id != int(self.creator.id) and
            subscriber_id != int(self.parent_response.user_id)
        )

    def send_response_on_followed_post_notification(self):
        """
        Send notification to followers of the thread/post
        except:
        Tread creator , response creator,
        """
        users = []
        page = 1
        has_more_subscribers = True

        while has_more_subscribers:

            subscribers = Subscription.fetch(self.thread.id, query_params={'page': page})
            if page <= subscribers.num_pages:
                for subscriber in subscribers.collection:
                    # Check if the subscriber is not the thread creator or response creator
                    subscriber_id = int(subscriber.get('subscriber_id'))
                    # do not send notification to the user who created the response and the thread
                    if self._check_if_subscriber_is_not_thread_or_content_creator(subscriber_id):
                        users.append(subscriber_id)
            else:
                has_more_subscribers = False
            page += 1
        # Remove duplicate users from the list of users to send notification
        users = list(set(users))
        if not self.parent_id:
            self._send_notification(users, "response_on_followed_post")
        else:
            self._send_notification(
                users,
                "comment_on_followed_post",
                extra_context={"author_name": self.parent_response.username}
            )

    def _create_cohort_course_audience(self):
        """
        Creates audience based on user cohort and role
        """
        course_key_str = str(self.course.id)
        discussion_cohorted = is_discussion_cohorted(course_key_str)

        # Retrieves cohort divided discussion
        discussion_settings = CourseDiscussionSettings.objects.get(course_id=course_key_str)
        divided_course_wide_discussions, divided_inline_discussions = get_divided_discussions(
            self.course,
            discussion_settings
        )

        # Checks if post has any cohort assigned
        group_id = self.thread.attributes['group_id']
        if group_id is not None:
            group_id = int(group_id)

        # Course wide topics
        topic_id = self.thread.attributes['commentable_id']
        all_topics = divided_inline_discussions + divided_course_wide_discussions
        topic_divided = topic_id in all_topics or discussion_settings.always_divide_inline_discussions

        user_ids = []
        if discussion_cohorted and topic_divided and group_id is not None:
            users_in_cohort = CourseUserGroup.objects.filter(
                course_id=course_key_str, id=group_id
            ).values_list('users__id', flat=True)
            user_ids.extend(users_in_cohort)

            privileged_roles = [FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA]
            privileged_users = Role.objects.filter(
                name__in=privileged_roles,
                course_id=course_key_str
            ).values_list('users__id', flat=True)
            user_ids.extend(privileged_users)

            staff_users = CourseStaffRole(self.course.id).users_with_role().values_list('id', flat=True)
            user_ids.extend(staff_users)

            admin_users = CourseInstructorRole(self.course.id).users_with_role().values_list('id', flat=True)
            user_ids.extend(admin_users)
        else:
            user_ids = CourseEnrollment.objects.filter(
                course__id=course_key_str, is_active=True
            ).values_list('user__id', flat=True)

        unique_user_ids = list(set(user_ids))
        if self.creator.id in unique_user_ids:
            unique_user_ids.remove(self.creator.id)
        return unique_user_ids

    def send_new_thread_created_notification(self):
        """
        Send notification based on notification_type
        """
        thread_type = self.thread.attributes['thread_type']
        notification_type = (
            "new_question_post"
            if thread_type == "question"
            else ("new_discussion_post" if thread_type == "discussion" else "")
        )
        if notification_type not in ['new_discussion_post', 'new_question_post']:
            raise ValueError(f'Invalid notification type {notification_type}')

        user_ids = self._create_cohort_course_audience()
        context = {
            'username': self.creator.username,
            'post_title': self.thread.title
        }
        self._send_notification(user_ids, notification_type, context)


def is_discussion_cohorted(course_key_str):
    """
    Returns if the discussion is divided by cohorts
    """
    cohort_settings = CourseCohortsSettings.objects.get(course_id=course_key_str)
    discussion_settings = CourseDiscussionSettings.objects.get(course_id=course_key_str)
    return cohort_settings.is_cohorted and discussion_settings.always_divide_inline_discussions
