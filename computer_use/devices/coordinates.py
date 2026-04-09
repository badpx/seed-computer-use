"""Shared coordinate normalization for device commands."""

from __future__ import annotations

import re
from typing import Any

from .base import DeviceCommand


def normalize_command_coordinates(
    command: DeviceCommand,
    *,
    image_width: int,
    image_height: int,
    model_image_width: int,
    model_image_height: int,
    coordinate_space: str,
    coordinate_scale: float,
) -> DeviceCommand:
    payload = dict(command.payload or {})

    if 'x' in payload and 'y' in payload and 'point' not in payload:
        payload['point'] = [payload.pop('x'), payload.pop('y')]

    for key in ('point', 'start_point', 'end_point', 'start_box', 'end_box'):
        if key in payload:
            payload[key] = _normalize_coordinate_value(
                payload[key],
                image_width=image_width,
                image_height=image_height,
                model_image_width=model_image_width,
                model_image_height=model_image_height,
                coordinate_space=coordinate_space,
                coordinate_scale=coordinate_scale,
            )

    metadata = dict(command.metadata or {})
    metadata.update(
        {
            'coordinate_space': 'pixel',
            'coordinate_scale': 1.0,
            'normalized_coordinates': True,
            'frame_image_width': int(image_width),
            'frame_image_height': int(image_height),
        }
    )

    return DeviceCommand(
        command_type=command.command_type,
        payload=payload,
        metadata=metadata,
    )


def normalize_scroll_direction(
    command: DeviceCommand,
    *,
    natural_scroll: bool,
) -> DeviceCommand:
    if command.command_type != 'scroll' or not natural_scroll:
        return command

    payload = dict(command.payload or {})
    direction = str(payload.get('direction', '')).strip().lower()
    opposite_directions = {
        'up': 'down',
        'down': 'up',
        'left': 'right',
        'right': 'left',
    }
    if direction in opposite_directions:
        payload['direction'] = opposite_directions[direction]

    return DeviceCommand(
        command_type=command.command_type,
        payload=payload,
        metadata=dict(command.metadata or {}),
    )


def _normalize_coordinate_value(
    value: Any,
    *,
    image_width: int,
    image_height: int,
    model_image_width: int,
    model_image_height: int,
    coordinate_space: str,
    coordinate_scale: float,
):
    parsed = _parse_coordinate_value(value)
    if parsed is None:
        return value
    if len(parsed) == 2:
        return _convert_point(
            parsed[0],
            parsed[1],
            image_width=image_width,
            image_height=image_height,
            model_image_width=model_image_width,
            model_image_height=model_image_height,
            coordinate_space=coordinate_space,
            coordinate_scale=coordinate_scale,
        )
    if len(parsed) == 4:
        x1, y1 = _convert_point(
            parsed[0],
            parsed[1],
            image_width=image_width,
            image_height=image_height,
            model_image_width=model_image_width,
            model_image_height=model_image_height,
            coordinate_space=coordinate_space,
            coordinate_scale=coordinate_scale,
        )
        x2, y2 = _convert_point(
            parsed[2],
            parsed[3],
            image_width=image_width,
            image_height=image_height,
            model_image_width=model_image_width,
            model_image_height=model_image_height,
            coordinate_space=coordinate_space,
            coordinate_scale=coordinate_scale,
        )
        return [x1, y1, x2, y2]
    return value


def _convert_point(
    x: float,
    y: float,
    *,
    image_width: int,
    image_height: int,
    model_image_width: int,
    model_image_height: int,
    coordinate_space: str,
    coordinate_scale: float,
) -> list[int]:
    if str(coordinate_space).strip().lower() == 'pixel':
        abs_x = int(round(float(x) / float(model_image_width) * float(image_width)))
        abs_y = int(round(float(y) / float(model_image_height) * float(image_height)))
    else:
        abs_x = int(round(float(x) / float(coordinate_scale) * float(image_width)))
        abs_y = int(round(float(y) / float(coordinate_scale) * float(image_height)))
    return [abs_x, abs_y]


def _parse_coordinate_value(value: Any):
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        pair_match = re.fullmatch(
            r'[\[(]?\s*(-?(?:\d+(?:\.\d+)?|\.\d+))(?:[\s,]+)(-?(?:\d+(?:\.\d+)?|\.\d+))(?:[\s,]+(-?(?:\d+(?:\.\d+)?|\.\d+))[\s,]+(-?(?:\d+(?:\.\d+)?|\.\d+)))?\s*[\])]?',
            stripped,
        )
        if pair_match:
            numbers = [group for group in pair_match.groups() if group is not None]
            return [float(item) for item in numbers]
        return None
    if isinstance(value, (list, tuple)) and len(value) in {2, 4}:
        return [float(item) for item in value]
    return None
