# Copyright (c) 2016 99cloud, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""The server password extension."""

from webob import exc

from nova.api.openstack import common
from nova.api.openstack.compute.schemas import server_mem
from nova.api.openstack import extensions
from nova.api.openstack import wsgi
from nova.api import validation
from nova import compute
from nova import exception


ALIAS = 'os-server-mem-hottune'
authorize = extensions.os_compute_authorizer(ALIAS)


class ServerMemHottuneController(wsgi.Controller):
    """The Server Mem API controller for the OpenStack API."""
    def __init__(self):
        self.compute_api = compute.API(skip_policy_check=True)
        super(ServerMemHottuneController, self).__init__()

    @extensions.expected_errors(404)
    def index(self, req, server_id):
        context = req.environ['nova.context']
        authorize(context)
        instance = common.get_instance(self.compute_api, context, server_id)
        return dict(id=server_id, mem=instance.memory_mb)


class MemActionController(wsgi.Controller):

    def __init__(self, *args, **kwargs):
        super(MemActionController, self).__init__(*args, **kwargs)
        self.compute_api = compute.API(skip_policy_check=True)

    @wsgi.action('setMem')
    @wsgi.response(202)
    @extensions.expected_errors((400, 404, 409, 501))
    @validation.schema(server_mem.set_mem)
    def set_mem(self, req, id, body):
        context = req.environ['nova.context']
        authorize(context)

        mem = body['setMem']['mem']
        instance = common.get_instance(self.compute_api, context, id)
        try:
            self.compute_api.set_mem(context, instance, mem)
        except exception.InstanceUnknownCell as e:
            raise exc.HTTPNotFound(explanation=e.format_message())
        except exception.InstanceMemSetFailed as e:
            raise exc.HTTPConflict(explanation=e.format_message())
        except exception.InstanceInvalidState as e:
            common.raise_http_conflict_for_instance_invalid_state(
                e, 'setMem', id)
        except NotImplementedError:
            msg = _("Unable to set mem on instance")
            common.raise_feature_not_supported(msg=msg)


class ServerMemHottune(extensions.V21APIExtensionBase):
    """Server set mem support."""

    name = "ServerMemHottune"
    alias = ALIAS
    version = 1

    def get_resources(self):
        resources = [
            extensions.ResourceExtension(
                ALIAS, ServerMemHottuneController(),
                parent=dict(member_name='server', collection_name='servers'))]
        return resources

    def get_controller_extensions(self):
        controller = MemActionController()
        extension = extensions.ControllerExtension(self, 'servers', controller)
        return [extension]
