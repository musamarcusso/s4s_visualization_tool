__author__ = 'Musa Morena Marcusso Manhaes'

import numpy as np


class S4SMask(object):
    _MASK_LABELS = ['Circle', 'Rectangle', 'Range']

    _CIRCLE_PARAM_LABELS = {'radius': ('Radius', 0.1),
                            'center': ('Center', [0, 0, 0]),
                            'plane': ('Plane', 'xy'),
                            'is_exc': ('Is excluding?', False)}

    _RECT_PARAM_LABELS = {'low_point': ('Lower point', [0, 0]),
                          'upper_point': ('Upper point', [0, 0]),
                          'is_exc': ('Is excluding?', False)}

    _RANGE_PARAM_LABELS = {'axis': ('Axis', 'x'),
                           'lower': ('Lower', 0.0),
                           'upper': ('Upper', 0.0),
                           'is_exc': ('Is excluding?', False)}

    def __init__(self, id_number=-1, is_exc=False):
        if id_number == -1:
            raise ValueError('Set a positive id number for the mask')
        assert type(is_exc) is bool

        self._id = id_number

        self._mask_types = {}

        self._is_active = False

        for label in self._MASK_LABELS:
            self._mask_types[label] = False

        self._label = None

        self._circle_param = {'radius': 0,
                              'center': np.array([0.0, 0.0, 0.0]),
                              'plane': 'xy',
                              'is_exc': is_exc}

        self._circle_param_valid_test = {'radius': lambda x: x > 0,
                                         'center': lambda x: len(x) == 3,
                                         'plane': lambda x: x in ['xy', 'yz', 'xz'],
                                         'is_exc': lambda x: type(x) == bool}

        self._rect_param = {'low_point': [0.0, 0.0],
                            'upper_point': [0.0, 0.0],
                            'is_exc': is_exc}

        self._rect_param_valid_test = {'low_point': lambda x: (len(x) == 2 and x[0] < self._rect_param['upper_point'][0]
                                                              and x[1] < self._rect_param['upper_point'][1]),
                                       'upper_point': lambda x: (len(x) == 2 and x[0] > self._rect_param['low_point'][0]
                                                                and x[1] > self._rect_param['low_point'][1]),
                                       'is_exc': lambda x: type(x) == bool}

        self._range_param = {'axis': 'x',
                             'lower': 0.0,
                             'upper': 0.0,
                             'is_exc': is_exc}

        self._range_param_valid_test = {'axis': lambda x: x in ['x', 'y', 'z'],
                                        'lower': lambda x: x is not None and x < self._range_param['upper'],
                                        'upper': lambda x: x is not None and x > self._range_param['lower'],
                                        'is_exc': lambda x: type(x) == bool}

    @classmethod
    def get_mask_labels(cls):
        return cls._MASK_LABELS

    @classmethod
    def get_circle_mask_param_labels(cls):
        return cls._CIRCLE_PARAM_LABELS

    @classmethod
    def get_rect_mask_param_labels(cls):
        return cls._RECT_PARAM_LABELS

    @classmethod
    def get_range_mask_param_labels(cls):
        return cls._RANGE_PARAM_LABELS

    @property
    def label(self):
        return self._label

    @property
    def is_excluding(self):
        if self.is_circle_type:
            return self._circle_param['is_exc']
        elif self.is_range_type:
            return self._range_param['is_exc']
        elif self.is_rect_type:
            return self._rect_param['is_exc']
        else:
            return False

    @is_excluding.setter
    def is_excluding(self, flag):
        assert type(flag) == bool, 'Flag must be a boolean'
        if self.is_circle_type:
            self._circle_param['is_exc'] = flag
        elif self.is_range_type:
            self._range_param['is_exc'] = flag
        elif self.is_rect_type:
            self._rect_param['is_exc'] = flag

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, flag):
        if flag not in [True, False]:
            return
        self._is_active = flag

    @property
    def is_circle_type(self):
        return self._mask_types['Circle']

    @property
    def is_rect_type(self):
        return self._mask_types['Rectangle']

    @property
    def is_range_type(self):
        return self._mask_types['Range']

    def get_mask_type(self):
        for key in self._mask_types:
            if self._mask_types[key]:
                return key
        return None

    def _set_mask_type(self, mask_name):
        self._label = mask_name
        for key in self._mask_types:
            self._mask_types[key] = key == mask_name

    def set_rect_type(self):
        self._set_mask_type('Rectangle')

    def set_circle_type(self):
        self._set_mask_type('Circle')

    def set_range_type(self):
        self._set_mask_type('Range')

    def get_param_values(self):
        param = {}
        if self.is_circle_type:
            for key in self._circle_param:
                param[self._CIRCLE_PARAM_LABELS[key][0]] = self._circle_param[key]
        elif self.is_range_type:
            for key in self._range_param:
                param[self._RANGE_PARAM_LABELS[key][0]] = self._range_param[key]
        elif self.is_rect_type:
            for key in self._rect_param:
                param[self._RECT_PARAM_LABELS[key][0]] = self._rect_param[key]

        return param

    def set_circle_param(self, radius, center, plane):
        if type(radius) is not float:
            raise TypeError('The radius must be of float type')
        if type(plane) is not str and plane not in ['xy', 'yz', 'zx']:
            raise ValueError('The plane option has to be either xy, yz or zx')
        if type(center) is not list:
            raise TypeError('The center of the circle must be a list of three elements')
        if len(center) != 3:
            raise ValueError('The center position must have three elements')

        self.set_circle_type()
        self._circle_param['radius'] = radius
        self._circle_param['center'] = np.array(center)
        self._circle_param['plane'] = plane

    def set_rect_param(self, low_point, upper_point):
        if type(low_point) is not list or type(upper_point) is not list:
            raise TypeError('Lower and upper points must be of list type')
        if len(low_point) != 2 or len(upper_point) != 2:
            raise ValueError('The input lists must have two elements each (XY-plane)')
        if low_point[0] >= upper_point[0] or low_point[1] >= upper_point[1]:
            raise ValueError('Lower point is not lower than the upper point')
        self.set_rect_type()
        self._rect_param['low_point'] = np.array(low_point)
        self._rect_param['upper_point'] = np.array(upper_point)

    def set_range_param(self, lower, upper, axis):
        if type(lower) is not float or type(upper) is not float:
            raise TypeError('The range values must be of float type')
        if lower >= upper:
            raise ValueError('The lower value is not lower than the upper one')
        if axis not in ['x', 'y', 'z']:
            raise ValueError('The axis option can be x, y or z')

        self.set_range_type()
        self._range_param['lower'] = lower
        self._range_param['upper'] = upper
        self._range_param['axis'] = axis

    def set_param(self, label, new_value):
        key = ''
        if self.is_circle_type:
            for item in self._CIRCLE_PARAM_LABELS:
                if label == self._CIRCLE_PARAM_LABELS[item][0]:
                    key = item
            if len(key) and self._circle_param_valid_test[key](new_value):
                self._circle_param[key] = new_value
            else:
                return False
        elif self.is_rect_type:
            for item in self._RECT_PARAM_LABELS:
                if label == self._RECT_PARAM_LABELS[item][0]:
                    key = item
            if len(key) and self._rect_param_valid_test[key](new_value):
                self._rect_param[key] = new_value
            else:
                return False
        elif self.is_range_type:
            for item in self._RANGE_PARAM_LABELS:
                if label == self._RANGE_PARAM_LABELS[item][0]:
                    key = item
            if len(key) and self._range_param_valid_test[key](new_value):
                self._range_param[key] = new_value
            else:
                return False
        return True

    def test_point(self, x, y, z):
        if not self.is_circle_type and not self.is_rect_type and not self.is_range_type:
            raise AttributeError('No mask type option was set')

        if type(x) != np.ndarray or type(y) != np.ndarray or type(z) != np.ndarray:
            raise TypeError('Input matrices must be of type numpy.ndarray')

        if x.shape[0] != y.shape[0] or x.shape[0] != z.shape[0] or x.shape[1] != y.shape[1] or x.shape[1] != z.shape[1]:
            raise ValueError('Input matrices must have the same size')

        if self.is_circle_type:
            center = self._circle_param['center']
            radius = self._circle_param['radius']
            p1 = 0
            p2 = 1

            if self._circle_param['plane'] == 'xy':
                p1 = 0
                p2 = 1
                if self.is_excluding:
                    return np.sqrt((x - center[p1])**2 + (y - center[p2])**2) >= radius
                else:
                    return np.sqrt((x - center[p1])**2 + (y - center[p2])**2) < radius
            elif self._circle_param['plane'] == 'yz':
                p1 = 1
                p2 = 2
                if self.is_excluding:
                    z[np.isnan(z)] = 0
                    return np.sqrt((y - center[p1])**2 + (z - center[p2])**2) >= radius
                else:
                    z[np.isnan(z)] = radius + 1000
                    return np.sqrt((y - center[p1])**2 + (z - center[p2])**2) < radius
            elif self._circle_param['plane'] == 'zx':
                p1 = 0
                p2 = 2
                if self.is_excluding:
                    z[np.isnan(z)] = 0
                    return np.sqrt((x - center[p1])**2 + (z - center[p2])**2) >= radius
                else:
                    z[np.isnan(z)] = radius + 1000
                    return np.sqrt((x - center[p1])**2 + (z - center[p2])**2) < radius

        elif self.is_rect_type:
            if self.is_excluding:
                test = x <= np.min([self._rect_param['low_point'][0], self._rect_param['upper_point'][0]])
                test = np.logical_or(test,
                                     x >= np.max([self._rect_param['low_point'][0],
                                                  self._rect_param['upper_point'][0]]))
                test = np.logical_or(test,
                                     y <= np.min([self._rect_param['low_point'][1],
                                                  self._rect_param['upper_point'][1]]))
                test = np.logical_or(test,
                                     y >= np.max([self._rect_param['low_point'][1],
                                                  self._rect_param['upper_point'][1]]))
            else:
                test = x > np.min([self._rect_param['low_point'][0], self._rect_param['upper_point'][0]])
                test = np.logical_and(test,
                                      x < np.max([self._rect_param['low_point'][0],
                                                  self._rect_param['upper_point'][0]]))
                test = np.logical_and(test,
                                      y > np.min([self._rect_param['low_point'][1],
                                                  self._rect_param['upper_point'][1]]))
                test = np.logical_and(test, y < np.max([self._rect_param['low_point'][1],
                                                        self._rect_param['upper_point'][1]]))
            return test

        elif self.is_range_type:
            lower = self._range_param['lower']
            upper = self._range_param['upper']

            if self.is_excluding:
                if self._range_param['axis'] == 'x':
                    return np.logical_or(x < lower, x > upper)
                elif self._range_param['axis'] == 'y':
                    return np.logical_or(y < lower, y > upper)
                elif self._range_param['axis'] == 'z':
                    z[np.isnan(z)] = (upper - lower) / 2.0
                    return np.logical_or(z < lower, z > upper)
            else:
                if self._range_param['axis'] == 'x':
                    return np.logical_and(x >= lower, x <= upper)
                elif self._range_param['axis'] == 'y':
                    return np.logical_and(y >= lower, y <= upper)
                elif self._range_param['axis'] == 'z':
                    z[np.isnan(z)] = upper + 100
                    return np.logical_and(z >= lower, z <= upper)

        return False
