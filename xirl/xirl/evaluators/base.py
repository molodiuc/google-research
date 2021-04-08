# coding=utf-8
# Copyright 2021 The Google Research Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Base evaluator."""

import abc
from typing import List, Optional, Union

import dataclasses
import numpy as np
from torchkit import Logger
from xirl.models import SelfSupervisedOutput


@dataclasses.dataclass
class EvaluatorOutput:
  """The output of an evaluator."""

  # An evaluator does not necessarily generate all fields below. For example,
  # some evaluators like Kendalls Tau return a scalar and image metric, while
  # TwoWayCycleConsistency only generates a scalar metric.
  scalar: Optional[Union[float, List[float]]] = None
  image: Optional[Union[np.ndarray, List[np.ndarray]]] = None
  video: Optional[Union[np.ndarray, List[np.ndarray]]] = None

  @staticmethod
  def _assert_same_attrs(list_out):
    """Ensures a list of this class instance have the same attributes."""

    def _not_none(o):
      return [getattr(o, a) is not None for a in ["scalar", "image", "video"]]

    expected = _not_none(list_out[0])
    for o in list_out[1:]:
      actual = _not_none(o)
      assert np.array_equal(expected, actual)

  @staticmethod
  def merge(list_out):
    """Merge a list of this class instance into one."""
    # We need to make sure that all elements of the list have the same
    # non-empty (i.e. != None) attributes.
    EvaluatorOutput._assert_same_attrs(list_out)
    # At this point, we're confident that we only need to check the
    # attributes of the first member of the list to guarantee the same
    # availability for *all* other members of the list.
    scalars = None
    if list_out[0].scalar is not None:
      scalars = [o.scalar for o in list_out]
    images = None
    if list_out[0].image is not None:
      images = [o.image for o in list_out]
    videos = None
    if list_out[0].video is not None:
      videos = [o.video for o in list_out]
    return EvaluatorOutput(scalars, images, videos)

  def log(self, logger, global_step, name,
          prefix):
    """Log the attributes to tensorboard."""
    if self.scalar is not None:
      if isinstance(self.scalar, list):
        self.scalar = np.mean(self.scalar)
      logger.log_scalar(self.scalar, global_step, name, prefix)
    if self.image is not None:
      if isinstance(self.image, list):
        for i, image in enumerate(self.image):
          logger.log_image(image, global_step, name + f"_{i}", prefix)
      else:
        logger.log_image(self.image, global_step, name, prefix)
    if self.video is not None:
      if isinstance(self.video, list):
        for i, video in enumerate(self.video):
          logger.log_video(video, global_step, name + f"_{i}", prefix)
      else:
        logger.log_video(self.video, global_step, name, prefix)


class Evaluator(abc.ABC):
  """Base class for evaluating a self-supervised model on downstream tasks.

  Subclasses must implement the `_evaluate` method.
  """

  def __init__(self, inter_class):
    self.inter_class = inter_class

  @abc.abstractmethod
  def evaluate(self, outs):
    """Evaluate the downstream task in embedding space.

    Args:
      outs: A list of outputs generated by the model on the downstream dataset.
        :meta public:
    """
    pass