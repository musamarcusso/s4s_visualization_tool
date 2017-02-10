__author__ = 'Musa Morena Marcusso Manhaes'

import os
from copy import deepcopy
import numpy as np
from scipy.optimize import leastsq
from scipy.interpolate import griddata
import datetime
import re
from time import time
import S4SMessageHandler
import S4SMask


def plane_eval(param, x, y):
    if type(x) == np.ndarray and type(y) == np.ndarray:
        z = (-param[3] - param[0] * x.flatten() - param[1] * y.flatten()) / param[2]
    else:
        z = (-param[3] - param[0] * x - param[1] * y) / param[2]
    return z


class S4SData(object):
    _MAX_POINTS = 200

    def __init__(self):
        self._details = {'filename': '',
                         'dir': '',
                         'n_points': 0,
                         'center_of_mass': np.array([0.0, 0.0, 0.0]),
                         'max': '',
                         'min': '',
                         'range_x': 0,
                         'range_y': 0,
                         'range_z': 0,
                         'file_size': 0.0,
                         'last_modified': ' '}
        self._details_labels = {'filename': 'Filename',
                                'dir': 'Directory',
                                'n_points': 'Number of points',
                                'center_of_mass': 'Center of mass [mm]',
                                'max': 'Maximum value [mm]',
                                'min': 'Minimum value [mm]',
                                'range_x': 'Range in X [mm]',
                                'range_y': 'Range in Y [mm]',
                                'range_z': 'Range in Z [mm]',
                                'file_size': 'File size',
                                'last_modified': 'Last modified'}

        self._label = ''

        self._comment = ''

        # Filtering mask to remove points that are not needed for the analysis
        self._mask = None

        self._color = None
        # Rotation angles (Euler's angles) to remove the tilt of the point cloud
        self._rot = np.array([0, 0, 0])
        # Translation vector regarding the center of mass
        self._trans = np.array([0, 0, 0])
        # Set the list of filtering masks that set the ROI
        self._masks = {}

        self._mask_index = 0

        self._plane_param = [0, 0, 0, 0]

        self._trans_range = [-100.0, 100.0]

        self._rot_range = [-180.0, 180.0]

        self._step = 1

        self._has_mask_changed = False

        self._use_plane = False

        self._always_remove_offset = False

        self._uploaded_data = []

        self._x = None

        self._y = None

        self._z = None

        self._thread_is_running = False

        self._message_handler = S4SMessageHandler.S4SMessageHandler.get_instance()


    @classmethod
    def get_mask_labels(cls):
        return S4SMask.S4SMask.get_mask_labels()

    @classmethod
    def get_circle_mask_param_labels(cls):
        return S4SMask.S4SMask.get_circle_mask_param_labels()

    @classmethod
    def get_rect_mask_param_labels(cls):
        return S4SMask.S4SMask.get_rect_mask_param_labels()

    @classmethod
    def get_range_mask_param_labels(cls):
        return S4SMask.S4SMask.get_range_mask_param_labels()

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, new_label):
        assert type(new_label) == str
        self._label = new_label
        self.store_ini_file()
        self._message_handler.push_message('Data', 'info', 'New label: ' + self._label)

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, new_comment):
        assert type(new_comment) == str
        self._comment = new_comment
        self.store_ini_file()
        self._message_handler.push_message('Data', 'info', 'New comment: ' + self._comment)

    @property
    def thread_is_running(self):
        return self._thread_is_running

    @thread_is_running.setter
    def thread_is_running(self, flag):
        assert type(flag) is bool
        self._thread_is_running = flag

    @property
    def is_data_loaded(self):
        return self._x is not None and self._y is not None and self._z is not None

    @property
    def always_remove_offset(self):
        return self._always_remove_offset

    @property
    def use_plane(self):
        return self._use_plane

    @use_plane.setter
    def use_plane(self, is_active):
        if type(is_active) is not bool:
            raise TypeError
        self._use_plane = is_active
        if self._use_plane:
            self.calc_fitting_plane()

    @always_remove_offset.setter
    def always_remove_offset(self, is_active):
        if type(is_active) is not bool:
            raise TypeError
        self._always_remove_offset = is_active

    @property
    def trans_range(self):
        return self._trans_range

    @property
    def rot_range(self):
        return self._rot_range

    @property
    def translation_vector(self):
        return self._trans

    @property
    def rotation_vector(self):
        return self._rot

    @property
    def step(self):
        if self._step == 0 and self._x is not None:
            self._step = np.fix(np.min([self._x.shape[0], self._x.shape[1]]) / self._MAX_POINTS)
            if self._step == 0:
                self._step = 1
        return self._step

    @step.setter
    def step(self, new_step):
        if new_step < 1:
            raise ValueError('The step must be greater than zero')
        if self._x is None or self._y is None or self._z is None:
            raise ValueError('No data has been loaded')
        if new_step > self._x.shape[0] or new_step > self._x.shape[1]:
            raise ValueError('The step must be smaller than the number of points in the point cloud, value=' + str(new_step))
        self._step = int(new_step)

    @property
    def filename(self):
        return self._details['filename']

    @filename.setter
    def filename(self, new_file):
        try:
            directory, filename = new_file
        except:
            raise TypeError('Input must be a tuple')

        if type(filename) is not str or type(directory) is not str:
            raise TypeError('The filename input must be a string')
        if not os.path.isfile(os.path.join(directory, filename)):
            raise ValueError('Invalid path or filename')

        self._details['filename'] = filename
        self._details['dir'] = directory

    @property
    def details_list(self):
        return deepcopy(self._details)

    @property
    def details_labels(self):
        return deepcopy(self._details_labels)

    @property
    def range_x(self):
        if self._x is not None and self._y is not None and self._z is not None:
            mask = self._get_mask()
            return [self._x[mask].min(), self._x[mask].max()]
        else:
            return [-1, -1]

    @property
    def range_y(self):
        if self._x is not None and self._y is not None and self._z is not None:
            mask = self._get_mask()
            return [self._y[mask].min(), self._y[mask].max()]
        else:
            return [-1, -1]

    @property
    def range_z(self):
        if self._x is not None and self._y is not None and self._z is not None:
            mask = self._get_mask()
            return [self._z[mask].min(), self._z[mask].max()]
        else:
            return [-1, -1]

    @property
    def range_c(self):
        if self._x is not None and self._y is not None and self._z is not None:
            if not self._use_plane:
                return self.range_z
            else:
                mask = self._get_mask()
                return [self._color[mask].min(), self._color[mask].max()]
        else:
            return [-1, -1]

    @property
    def n_masks(self):
        return len(self._masks.keys())

    @property
    def data(self):
        if self._x is not None:
            if self._always_remove_offset:
                self.calc_center_of_mass()
                cm = self._details['center_of_mass']
            else:
                cm = [0.0, 0.0, 0.0]

            z = deepcopy(self._z)
            if np.count_nonzero(self._mask) == 0:
                self.disable_all_masks()

            z[np.logical_not(self._mask)] = np.nan

            return self._x[::self._step, ::self._step] - cm[0], \
                   self._y[::self._step, ::self._step] - cm[1], \
                   z[::self._step, ::self._step] - cm[2], \
                   self._color[::self._step, ::self._step] if self._use_plane else self._z[::self._step, ::self._step]
        else:
            return None, None, None, None

    @property
    def plane(self):
        if self._x is not None and self._use_plane:
            mask = self._get_mask()
            x, y = np.meshgrid([self._x[mask].min() - 0.2, self._x[mask].max() + 0.2],
                               [self._y[mask].min() - 0.2, self._y[mask].max() + 0.2])
            plane = np.ones(shape=x.shape)
            for i in range(plane.shape[0]):
                for j in range(plane.shape[1]):
                    plane[i, j] = plane_eval(self._plane_param, x[i, j], y[i, j])
            return x, y, plane
        else:
            return None

    @property
    def center_of_mass(self):
        self.calc_center_of_mass()
        return self._details['center_of_mass']

    def _get_mask(self):
        self.update_mask()
        self._step = np.fix(np.max([self._x.shape[0], self._x.shape[1]]) / self._MAX_POINTS)
        if self._step < 1:
            self._step = 1
        mask = np.logical_and(self._mask, np.logical_not(np.isnan(self._z)))
        if np.count_nonzero(mask) == 0:
            self.disable_all_masks()
            mask = np.logical_not(np.isnan(self._z))
            self._message_handler.push_message('Data', 'error', 'Reseting all masks...filter excluded all points')
        return mask

    def get_mask_type(self, index):
        if index not in self._masks:
            return None
        return self._masks[index].get_mask_type()

    def reset_filters(self):
        self._masks = {}
        self._mask_index = 0
        self._has_mask_changed = True
        self.update_mask()

    def get_mask_info(self, index):
        if index not in self._masks:
            return None
        return self._masks[index].get_param_values()

    def get_mask_label(self, index):
        if index not in self._masks:
            return None
        return self._masks[index].label

    def get_mask_indexes(self):
        return self._masks.keys()

    def disable_all_masks(self):
        if np.count_nonzero(self._mask) == 0:
            if len(self._masks.keys()) > 0:
                for key in self._masks:
                    self._masks[key].is_active = False
            self._mask = np.logical_not(np.isnan(self._z))

    def add_circle_mask(self, radius, center, plan, is_exc):
        try:
            # Create new circular mask with the given parameters
            new_mask = S4SMask.S4SMask(id_number=self._mask_index, is_exc=is_exc)
            new_mask.set_circle_param(radius, center, plan)
            # Add the new mask to the list
            self._masks[self._mask_index] = new_mask
            self._mask_index += 1
            # Update the data mask
            self._has_mask_changed = True
            self.update_mask()
            return self._mask_index - 1
        except [ValueError, TypeError, AttributeError]:
            return -1

    def calc_color(self):
        self._color = np.ones(shape=self._z.shape)
        self._color = self._z - (-self._plane_param[3] - self._plane_param[0] * self._x - self._plane_param[1] *
                               self._y) / self._plane_param[2]
        self._color[np.logical_not(self._mask)] = np.nan

    def calc_fitting_plane(self):
        mask = self._get_mask()
        param = leastsq(lambda x: self._z[mask].flatten() - plane_eval(x, self._x[mask], self._y[mask]),
                        [1, 1, 1, 1],
                        full_output=True)
        self._plane_param = param[0]
        self._message_handler.push_message('Data', 'info', 'New parameters for the fitting plane calculated!')

        self.calc_color()
        return True

    def add_rect_mask(self, low_point, upper_point, is_exc):
        try:
            # Create new rectangular mask with the given parameters
            new_mask = S4SMask.S4SMask(id_number=self._mask_index, is_exc=is_exc)
            new_mask.set_rect_param(low_point, upper_point)
            # Add the new mask to the list
            self._masks[self._mask_index] = new_mask
            self._mask_index += 1
            # Update the data mask
            self._has_mask_changed = True
            self.update_mask()
            return self._mask_index - 1
        except [ValueError, TypeError, AttributeError]:
            return -1

    def delete_all_masks(self):
        del self._masks
        self._masks = {}
        self._has_mask_changed = True
        self.update_mask()

    def add_range_mask(self, lower, upper, axis, is_exc):
        try:
            # Create new range mask with the given parameters
            new_mask = S4SMask.S4SMask(id_number=self._mask_index, is_exc=is_exc)
            new_mask.set_range_param(lower, upper, axis)
            # Add the new mask to the list
            self._masks[self._mask_index] = new_mask
            self._mask_index += 1
            # Update the data mask
            self._has_mask_changed = True
            self.update_mask()
            return self._mask_index - 1
        except [ValueError, TypeError, AttributeError]:
            return -1

    def set_mask_param(self, index, label, new_value):
        if index not in self._masks:
            return False
        self._has_mask_changed = True
        return self._masks[index].set_param(label, new_value)

    def update_mask(self, force=False):
        if not self._has_mask_changed and not force:
            return True
        if self._x is None or self._mask is None:
            self._message_handler.push_message('Data', 'error', 'The data matrix was not initialized')
            raise ValueError('The data matrix was not initialized')

        self._mask = np.logical_not(np.isnan(self._z))

        if len(self._masks.keys()):
            for key in self._masks:
                mask = self._masks[key]
                if not mask.is_active:
                    continue
                self._mask = np.logical_and(self._mask, mask.test_point(self._x, self._y, deepcopy(self._z)))

        self._has_mask_changed = False
        if self._use_plane:
            self.calc_fitting_plane()

        if np.count_nonzero(self._mask) == 0:
            self.disable_all_masks()

        self._message_handler.push_message('Data', 'info', 'Mask updated')
        return True

    def get_rotation_matrix(self):
        pass

    def set_translation_rel(self, x=0.0, y=0.0, z=0.0):
        if type(x) is not float or type(y) is not float or type(z) is not float:
            raise TypeError('Input arguments must be of float type')
        self._trans[0] += x
        self._trans[1] += y
        self._trans[2] += z

    def set_translation_abs(self, x=0.0, y=0.0, z=0.0):
        if type(x) is not float or type(y) is not float or type(z) is not float:
            raise TypeError('Input arguments must be of float type')
        self._trans[0] = x
        self._trans[1] = y
        self._trans[2] = z

    def set_rotation_rel(self, alpha=0.0, beta=0.0, gamma=0.0):
        pass

    def set_rotation_abs(self, alpha=0.0, beta=0.0, gamma=0.0):
        pass

    def reset_translation(self):
        self._trans[:] = 0.0

    def reset_rotation(self):
        self._rot[:] = 0.0

    def calc_center_of_mass(self):
        if self._x is None or self._y is None or self._z is None or self._mask is None:
            raise TypeError('No data has been loaded yet')
        mask = self._get_mask()
        self._details['center_of_mass'][0] = self._x[mask].mean()
        self._details['center_of_mass'][1] = self._y[mask].mean()
        self._details['center_of_mass'][2] = self._z[mask].mean()

    def remove_offset(self):
        if self._x is None or self._y is None or self._z is None:
            return False
        self.calc_center_of_mass()

        self._x -= self._details['center_of_mass'][0]
        self._y -= self._details['center_of_mass'][1]
        self._z -= self._details['center_of_mass'][2]

        self.calc_center_of_mass()
        return True

    def store_ini_file(self):
        if not os.path.isdir(self._details['dir']):
            return
        if not os.path.isfile(os.path.join(self._details['dir'], self._details['filename'])):
            return

        ini_file = self.get_ini_file()

        fid = open(os.path.join(self._details['dir'], ini_file), 'w')
        fid.write('label=' + self._label + '\n')
        fid.write('comment=' + self._comment + '\n')
        for s in self._details:
            if s in ['filename', 'dir']:
                continue
            fid.write(s + '=' + str(self._details[s]) + '\n')
        fid.close()

    def get_ini_file(self):
        if not os.path.isdir(self._details['dir']):
            return False
        if not os.path.isfile(os.path.join(self._details['dir'], self._details['filename'])):
            return False

        file_parts = self._details['filename'].split('.')
        ini_file = file_parts[0] + '.ini'
        return ini_file

    def get_npz_file(self):
        if not os.path.isdir(self._details['dir']):
            return False
        if not os.path.isfile(os.path.join(self._details['dir'], self._details['filename'])):
            return False

        file_parts = self._details['filename'].split('.')
        npz_file = file_parts[0] + '.npz'
        return npz_file

    def ini_file_exists(self):
        if not os.path.isdir(self._details['dir']):
            return False
        if not os.path.isfile(os.path.join(self._details['dir'], self._details['filename'])):
            return False

        ini_file = self.get_ini_file()

        return os.path.isfile(os.path.join(self._details['dir'], ini_file))

    def read_from_ini_file(self):
        if not os.path.isdir(self._details['dir']):
            return False
        if not os.path.isfile(os.path.join(self._details['dir'], self._details['filename'])):
            return False

        ini_file = self.get_ini_file()

        self._label = ''
        self._comment = ''

        if not os.path.isfile(os.path.join(self._details['dir'], ini_file)):
            return False

        fid = open(os.path.join(self._details['dir'], ini_file), 'r')
        for line in fid:
            s = line.split('=')

            if len(s) != 2:
                continue
            if 'label' in s:
                self._label = s[1].replace('\n', '')
            elif 'comment' in s:
                self._comment = s[1].replace('\n', '')

        fid.close()

        return True

    def open_file(self, comments='#', separator=' ', skip_row=0, callback_fcn=[]):
        self._thread_is_running = True

        self._message_handler.push_message('Data', 'info', 'Opening file, file=' + self._details['filename'])
        try:
            if not os.path.isdir(self._details['dir']):
                raise ValueError('Cannot open file, invalid directory')
            if not os.path.isfile(os.path.join(self._details['dir'], self._details['filename'])):
                raise ValueError('Cannot open file, invalid filename')
        except ValueError:
            self._message_handler.push_message('Data', 'error', 'Error opening measurement file')
            if len(callback_fcn) > 0:
                try:
                    for fcn in callback_fcn:
                        fcn()
                except:
                    self._message_handler.push_message('Data', 'error', 'Error calling the processor methods')
            return False

        data_file = os.path.join(self._details['dir'], self._details['filename'])

        try:
            file_obj = open(data_file, 'r')
            self._uploaded_data = None
            i = 0
            self._message_handler.push_message('Data', 'info', 'Reading measurement data...')
            start = time()
            message_sent = 0
            message_stamps = {5: lambda x: 'Still loading file, hang on... [Number of lines read = ' + str(x) + ']',
                              10: lambda x: 'Big file, this will take a while... [Number of  lines read = ' + str(x)
                                            + ']',
                              30: lambda x: 'Get a coffee, still not done loading... [Number of lines read = '
                                                       + str(x) + ']',
                              60: lambda x: 'Get a coffee, still not done loading... [Number of lines read = '
                                                       + str(x) + ']',
                              120: lambda x: 'Get a coffee, still not done loading... [Number of lines read = '
                                                       + str(i) + ']'}

            lines = file_obj.readlines()
            for line in lines:
                if not self._thread_is_running:
                    self._message_handler.push_message('Data', 'info', 'Stop loading file...')
                    return False

                stamp = time()
                if i < skip_row:
                    continue
                if line.find(comments) != -1:
                    continue
                i += 1
                for n in range(len(message_stamps.keys())):
                    key = message_stamps.keys()[n]
                    if stamp - start > key:
                        if n == 0 and message_sent == 0:
                            message_sent = key
                            message_stamps[key](i)
                        elif message_sent == message_stamps.keys()[n - 1]:
                            message_sent = key
                            message_stamps[key](i)

                if any(c.isalpha() for c in line) or not any(c.isdigit() for c in line):
                    continue

                elems = re.findall('[-+]?\d+.\d+', line)
                if len(elems) == 3:
                    num_line = [float(x) for x in elems]
                    if self._uploaded_data is None:
                        self._uploaded_data = np.array(num_line)
                    else:
                        self._uploaded_data = np.vstack((self._uploaded_data, num_line))
            self._message_handler.push_message('Data', 'info', 'All values stored...Generating matrices...')
            file_obj.close()
        except Exception, e:
            self._message_handler.push_message('Data', 'error',
                                               'Error loading file, error=' + str(e) + ', file=' +
                                               self._details['filename'])
            if len(callback_fcn) > 0:
                try:
                    for fcn in callback_fcn:
                        fcn()
                except:
                    self._message_handler.push_message('Data', 'error', 'Error calling the processor methods, '
                                                                        'error=' + e)
            self._thread_is_running = False
            return False

        if self._uploaded_data is None:
            return False

        # Load file as numpy matrix and set the mask selecting all points available
        min_x = self._uploaded_data[:, 0].min()
        max_x = self._uploaded_data[:, 0].max()
        min_y = self._uploaded_data[:, 1].min()
        max_y = self._uploaded_data[:, 1].max()
        min_z = self._uploaded_data[:, 2].min()
        max_z = self._uploaded_data[:, 2].max()

        self._details['range_x'] = max_x - min_x
        self._details['range_y'] = max_y - min_y
        self._details['range_z'] = max_z - min_z

        num_x = int((max_x - min_x) / 0.01)
        num_y = int((max_y - min_y) / 0.01)

        print 'range_x=%d, range_y=%d' % (max_x - min_x, max_y - min_y)
        print 'num_x=%d, num_y=%d' % (num_x, num_y)
        print 'x=', min_x, max_x
        print 'y=', min_y, max_y
        print ' '

        self._label = ''
        self._comment = ''
        if not self.read_from_ini_file():
            self.store_ini_file()

        self._x, self._y = np.meshgrid(np.linspace(min_x, max_x, max(num_x, 1000)),
                                       np.linspace(min_y, max_y, max(num_y, 1000)))

        self._z = griddata((self._uploaded_data[:, 0], self._uploaded_data[:, 1]),
                           self._uploaded_data[:, 2],
                           (self._x, self._y),
                           method='cubic')

        self._mask = np.ones(shape=self._z.shape, dtype=bool)
        self._color = None
        self._has_mask_changed = True
        self._step = np.fix(np.max([self._x.shape[0], self._x.shape[1]]) / self._MAX_POINTS)
        if self._step < 1:
            self._step = 1

        self.update_mask()
        if self._use_plane:
            self.calc_fitting_plane()
        # Calculate center of mass and remove the offset
        self.calc_center_of_mass()
        # Set the number of points to the details dictionary
        self._details['n_points'] = self._x.size

        last_modified = os.path.getmtime(data_file)
        self._details['last_modified'] = datetime.datetime.fromtimestamp(last_modified)
        size = int(round(os.path.getsize(data_file) * 0.001))
        self._details['file_size'] = str(size) + ' kB' if size < 1000  else str(float(size / 1000.0)) + ' MB'

        self._details['max'] = self._z[np.logical_not(np.isnan(self._z))].max()
        self._details['min'] = self._z[np.logical_not(np.isnan(self._z))].min()

        self.reset_filters()

        if len(callback_fcn) > 0:
            try:
                for fcn in callback_fcn:
                    fcn()
            except:
                self._message_handler.push_message('Data', 'error', 'Error calling the processor methods')
            finally:
                self._message_handler.push_message('Data', 'info', 'Measurement data loaded successfully')

        self._thread_is_running = False
        return True

    def set_mask_active(self, index, is_active):
        if len(self._masks) == 0:
            return True
        if index not in self._masks:
            return False

        self._masks[index].is_active = is_active
        self.update_mask()

    def is_mask_active(self, index):
        if len(self._masks) == 0:
            return True
        if index not in self._masks:
            return False
        self._has_mask_changed = True
        return self._masks[index].is_active



