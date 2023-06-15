# lint-amnesty, pylint: disable=missing-module-docstring
import logging
from rest_framework.generics import RetrieveUpdateDestroyAPIView, CreateAPIView
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404
from edx_api_doc_tools import schema_for
from drf_yasg import openapi

from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from common.djangoapps.util.json_request import expect_json_in_class_view

from ....api import course_author_access_required

from cms.djangoapps.contentstore.xblock_services import xblock_service
import cms.djangoapps.contentstore.toggles as contentstore_toggles

log = logging.getLogger(__name__)
toggles = contentstore_toggles
handle_xblock = xblock_service.handle_xblock

course_id_param = openapi.Parameter(
    "course_id", "path", description="Course ID", type=openapi.TYPE_STRING
)
usage_key_string_param = openapi.Parameter(
    "usage_key_string",
    "path",
    description="Usage Key String",
    type=openapi.TYPE_STRING,
    # required=False,
)


xblock_example_json = {
    "id": "block-v1:edX+110+1+type@vertical+block@8d18500afbd74cb688a41e9e41c83e37",
    "display_name": "Unit",
    "category": "vertical",
    "has_children": True,
    "edited_on": "Mar 07, 2018 at 07:26 UTC",
    "published": True,
    "published_on": "Mar 07, 2018 at 07:26 UTC",
    "studio_url": "/container/block-v1:edX+110+1+type@vertical+block@8d18500afbd74cb688a41e9e41c83e37",
    "released_to_students": True,
    "release_date": "Jan 01, 2020 at 00:00 UTC",
    "visibility_state": "needs_attention",
    "has_explicit_staff_lock": False,
    "start": "2020-01-01T00:00:00Z",
    "graded": False,
    "due_date": "",
    "due": None,
    "relative_weeks_due": None,
    "format": None,
    "course_graders": [
        "Homework",
        "Lab",
        "Midterm Exam",
        "Final Exam"
    ],
    "has_changes": True,
    "actions": {
        "deletable": True,
        "draggable": True,
        "childAddable": True,
        "duplicable": True
    },
    "explanatory_message": None,
    "group_access": {},
    "user_partitions": [
        {
            "id": 1452468171,
            "name": "Content Group Configuration",
            "scheme": "cohort",
            "groups": [
                {
                    "id": 450826036,
                    "name": "one",
                    "selected": False,
                    "deleted": False
                }
            ]
        },
        {
            "id": 50,
            "name": "Enrollment Track Groups",
            "scheme": "enrollment_track",
            "groups": [
                {
                    "id": 1,
                    "name": "Audit",
                    "selected": False,
                    "deleted": False
                },
                {
                    "id": 2,
                    "name": "Verified Certificate",
                    "selected": False,
                    "deleted": False
                }
            ]
        },
        {
            "id": 51,
            "name": "Feature-based Enrollments",
            "scheme": "content_type_gate",
            "groups": [
                {
                    "id": 1,
                    "name": "Limited-access Users",
                    "selected": False,
                    "deleted": False
                },
                {
                    "id": 2,
                    "name": "Full-access Users",
                    "selected": False,
                    "deleted": False
                }
            ]
        }
    ],
    "show_correctness": "always",
    "discussion_enabled": True,
    "data": "",
    "metadata": {
        "display_name": "Unit",
        "xml_attributes": {
            "filename": [
                "",
                None
            ]
        }
    },
    "ancestor_has_staff_lock": False,
    "user_partition_info": {
        "selectable_partitions": [
            {
                "id": 50,
                "name": "Enrollment Track Groups",
                "scheme": "enrollment_track",
                "groups": [
                    {
                        "id": 1,
                        "name": "Audit",
                        "selected": False,
                        "deleted": False
                    },
                    {
                        "id": 2,
                        "name": "Verified Certificate",
                        "selected": False,
                        "deleted": False
                    }
                ]
            },
            {
                "id": 1452468171,
                "name": "Content Group Configuration",
                "scheme": "cohort",
                "groups": [
                    {
                        "id": 450826036,
                        "name": "one",
                        "selected": False,
                        "deleted": False
                    }
                ]
            }
        ],
        "selected_partition_index": -1,
        "selected_groups_label": ""
    }
}


""" This could be an xblock schema for openapi. Obviously it is not complete.
# xblock_schema is an openapi Schema on the basis of xblock_example_json
xblock_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "id": openapi.Schema(type=openapi.TYPE_STRING),
        "display_name": openapi.Schema(type=openapi.TYPE_STRING),
        "category": openapi.Schema(type=openapi.TYPE_STRING),
        "has_children": openapi.Schema(type=openapi.TYPE_BOOLEAN),
        "edited_on": openapi.Schema(type=openapi.TYPE_STRING),
        "published": openapi.Schema(type=openapi.TYPE_BOOLEAN),
        "published_on": openapi.Schema(type=openapi.TYPE_STRING),
        "studio_url": openapi.Schema(type=openapi.TYPE_STRING),
        "released_to_students": openapi.Schema(type=openapi.TYPE_BOOLEAN),
        "release_date": openapi.Schema(type=openapi.TYPE_STRING),
        "visibility_state": openapi.Schema(type=openapi.TYPE_STRING),
        "has_explicit_staff_lock": openapi.Schema(type=openapi.TYPE_BOOLEAN),
        "start": openapi.Schema(type=openapi.TYPE_STRING),
        "graded": openapi.Schema(type=openapi.TYPE_BOOLEAN),
        "due_date": openapi.Schema(type=openapi.TYPE_STRING),
        "due": openapi.Schema(type=openapi.TYPE_STRING),
        "relative_weeks_due": openapi.Schema(type=openapi.TYPE_STRING),
        "format": openapi.Schema(type=openapi.TYPE_STRING),
        "course_graders": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(type=openapi.TYPE_STRING),
        ),
        "has_changes": openapi.Schema(type=openapi.TYPE_BOOLEAN),
        "actions": openapi.Schema(
            type=openapi.TYPE_OBJECT,
        ),
        "explanatory_message": openapi.Schema(type=openapi.TYPE_STRING),
        "group_access": openapi.Schema(type=openapi.TYPE_OBJECT),
        "user_partitions": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
            ),
        ),
        "show_correctness": openapi.Schema(type=openapi.TYPE_STRING),
        "discussion_enabled": openapi.Schema(type=openapi.TYPE_BOOLEAN),
        "data": openapi.Schema(type=openapi.TYPE_STRING),
        "metadata": openapi.Schema(
            type=openapi.TYPE_OBJECT,
        ),
        "ancestor_has_staff_lock": openapi.Schema(type=openapi.TYPE_BOOLEAN),
        "user_partition_info": openapi.Schema(
            type=openapi.TYPE_OBJECT,
        ),
    },
)
"""


@schema_for(
    "get",
    parameters={
        "course_id": openapi.Parameter(
            name="course_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            required=True,
            description="The course id of the XBlock to be retrieved.",
        ),
        "usage_key_string": openapi.Parameter(
            name="usage_key_string",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            required=True,
            description="The usage key of the XBlock to be retrieved.",
        ),
    },
    responses={
        200: openapi.Response(
            "XBlock",
            examples={
                "application/json": xblock_example_json,
            }
        ),
        403: openapi.Response('Forbidden: You need to have course author permissions for this course.'),
        404: openapi.Response('Not found: The requested XBlock does not exist.'),
    },
)
@schema_for(
    "post",
    parameters={
        "course_id": openapi.Parameter(
            name="course_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            required=True,
            description="The course id of the XBlock to be deleted.",
        ),
        "usage_key_string": openapi.Parameter(
            name="usage_key_string",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            required=True,
            description="The usage key of the XBlock to be deleted.",
        ),

    },
)
@schema_for(
    "delete",
    parameters={
        "course_id": openapi.Parameter(
            name="course_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            required=True,
            description="The course id of the XBlock to be deleted.",
        ),
        "usage_key_string": openapi.Parameter(
            name="usage_key_string",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            required=True,
            description="The usage key of the XBlock to be deleted.",
        ),
    },
)
@view_auth_classes()
class XblockView(DeveloperErrorViewMixin, RetrieveUpdateDestroyAPIView):
    """
    public REST API endpoint for the Studio Content API.
    course_key: required argument, needed to authorize course authors.
    usage_key_string (optional):
    xblock identifier, for example in the form of "block-v1:<course id>+type@<type>+block@<block id>"
    """

    def dispatch(self, request, *args, **kwargs):
        # TODO: probably want to refactor this to a decorator.
        """
        The dispatch method of a View class handles HTTP requests in general
        and calls other methods to handle specific HTTP methods.
        We use this to raise a 404 if the content api is disabled.
        """
        if not toggles.use_studio_content_api():
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    # pylint: disable=arguments-differ
    @course_author_access_required
    @expect_json_in_class_view
    def retrieve(self, request, course_key, usage_key_string=None):
        return handle_xblock(request, usage_key_string)

    @course_author_access_required
    @expect_json_in_class_view
    def update(self, request, course_key, usage_key_string=None):
        return handle_xblock(request, usage_key_string)

    @course_author_access_required
    @expect_json_in_class_view
    def partial_update(self, request, course_key, usage_key_string=None):
        return handle_xblock(request, usage_key_string)

    @course_author_access_required
    @expect_json_in_class_view
    def destroy(self, request, course_key, usage_key_string=None):
        return handle_xblock(request, usage_key_string)


@schema_for(
    "post",
    parameters=[
        course_id_param
    ],
    responses={
        404: 'Not found',
    },
)
@view_auth_classes()
class XblockPostView(DeveloperErrorViewMixin, CreateAPIView):
    """
    public rest API endpoint for the Studio Content API.
    course_key: required argument, needed to authorize course authors.
    usage_key_string (optional):
    xblock identifier, for example in the form of "block-v1:<course id>+type@<type>+block@<block id>"
    """

    def dispatch(self, request, *args, **kwargs):
        # TODO: probably want to refactor this to a decorator.
        """
        The dispatch method of a View class handles HTTP requests in general
        and calls other methods to handle specific HTTP methods.
        We use this to raise a 404 if the content api is disabled.
        """
        if not toggles.use_studio_content_api():
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    @csrf_exempt
    @course_author_access_required
    @expect_json_in_class_view
    def create(self, request, course_key, usage_key_string=None):
        return handle_xblock(request, usage_key_string)
