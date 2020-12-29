from rest_framework.views import APIView
from rest_framework.response import Response

from kernel.permissions.omnipotence import has_omnipotence_rights


class IsAdminRights(APIView):
    """
    This view is used to find if the user isAdmin(has omnipotence rights)
    """

    def get(self, request, format=None):
        response = Response(
            request.user is not None
            and has_omnipotence_rights(request.user)
        )
        return response
