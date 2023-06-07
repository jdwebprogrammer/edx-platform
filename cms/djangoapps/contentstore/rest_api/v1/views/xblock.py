# lint-amnesty, pylint: disable=missing-module-docstring
import logging
from rest_framework.generics import RetrieveUpdateDestroyAPIView, CreateAPIView
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404
from edx_api_doc_tools import schema_for, path_parameter, schema, parameter, string_parameter, ParameterLocation
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
    type=openapi.TYPE_NUMBER,
    # required=False,
)


@schema_for(
    "get",
    parameters=[
        course_id_param,
        usage_key_string_param,
    ],
    responses={
        404: 'Not found',
    },
)
@view_auth_classes()
class XblockView(DeveloperErrorViewMixin, RetrieveUpdateDestroyAPIView):
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
