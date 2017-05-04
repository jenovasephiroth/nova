# Copyright 2017 Tencent
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

from oslo_config import cfg
from oslo_log import log as logging

from nova.compute import power_state
from nova.compute import rpcapi as compute_rpcapi
from nova.compute import utils as compute_utils
from nova import exception
from nova.i18n import _
from nova import image
from nova import objects
from nova.scheduler import client as scheduler_client
from nova.scheduler import utils as scheduler_utils
from nova import servicegroup

LOG = logging.getLogger(__name__)


class LiveResizeTask(object):

    def __init__(self, context, image, instance, flavor, reservations):
        self.context = context
        self.instance = instance
        self.flavor = flavor
        self.image = image
        self.reservations = reservations
        self.compute_rpcapi = compute_rpcapi.ComputeAPI()

    def execute(self):
        self._check_instance_is_active()

        self.compute_rpcapi.live_resize_instance(
            self.context, self.image, self.instance, self.flavor,
            self.reservations)

    def _check_instance_is_active(self):
        if self.instance.power_state not in (power_state.RUNNING,
                                             power_state.PAUSED):
            raise exception.InstanceInvalidState(
                instance_uuid=self.instance.uuid,
                attr='power_state',
                state=self.instance.power_state,
                method='live resize')

    def rollback(self):
        raise NotImplementedError()


def execute(context, image, instance, flavor,
            reservations):
    task = LiveResizeTask(context, image, instance,
                          flavor, reservations)
    # TODO(johngarbutt) create a superclass that contains a safe_execute call
    return task.execute()
