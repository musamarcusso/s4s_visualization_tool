__author__ = 'Musa Morena Marcusso Manhaes'

import os
import S4SData
import S4SMessageHandler
from threading import Thread


class S4SProcessor(object):
    _DEFAULT_PATH_FILE = './config/default_path.txt'

    def __init__(self):
        self._message_handler = S4SMessageHandler.S4SMessageHandler.get_instance()
        try:
            file_path = open(self._DEFAULT_PATH_FILE)
            self._cur_directory = os.path.join(file_path.readline())
            self._cur_directory = self._cur_directory.replace('\n', '')
            file_path.close()
            if not os.path.isdir(self._cur_directory):
                raise ValueError
        except Exception, e:
            self._cur_directory = '.'
            self._message_handler.push_message('Processor', 'error', 'Invalid directory')

        self._cur_file = None
        self._data = S4SData.S4SData()
        self._callback_fcn = {'update_data': [],
                              'update_filter': [],
                              'is_loaded': []}

        self._are_threads_running = True
        self._tasks_thread = None
        self._loading_thread = None
        self._load_file_thread = None

    @property
    def current_directory(self):
        return self._cur_directory

    @current_directory.setter
    def current_directory(self, new_dir):
        if type(new_dir) is not str:
            raise TypeError('Directory path must be a string type')
        if not os.path.isdir(new_dir):
            raise ValueError('Invalid directory')
        self._cur_directory = new_dir

    @property
    def current_file(self):
        return self._cur_file

    @current_file.setter
    def current_file(self, new_file):
        if type(new_file) is not str:
            raise TypeError
        if type(self._cur_directory) is not str:
            raise TypeError('Directory has not been set')
        if not os.path.isdir(self._cur_directory) or not os.path.isfile(os.path.join(self._cur_directory, new_file)):
            raise ValueError('Invalid path or filename')
        self._cur_file = new_file
        self._data.filename = (self._cur_directory, self._cur_file)

    @property
    def data_details(self):
        return self._data.details_list

    @property
    def data_details_labels(self):
        return self._data.details_labels

    @property
    def translation_vector(self):
        return self._data.translation_vector

    @property
    def trans_range(self):
        return self._data.trans_range

    @property
    def rot_range(self):
        return self._data.rot_range

    @property
    def rotation_vector(self):
        return self._data.rotation_vector

    def remove_offset(self, is_active):
        self._data.always_remove_offset = is_active
        self.call_callbacks('update_data')

    def set_callback_fcn(self, label, fcn):
        if label not in self._callback_fcn:
            raise KeyError('The callback label does not exist')

        self._callback_fcn[label].append(fcn)

    def call_callbacks(self, label):
        if label not in self._callback_fcn:
            raise KeyError('The callback label does not exist')
        if len(self._callback_fcn[label]) == 0:
            return True
        for fcn in self._callback_fcn[label]:
            fcn()
        return True

    def store_cur_directory(self):
        assert os.path.isfile(self._DEFAULT_PATH_FILE)
        assert os.path.isdir(self._cur_directory)

        file = open(self._DEFAULT_PATH_FILE, 'w+')
        file.write(self._cur_directory)
        file.close()

    def is_data_loaded(self):
        return self._data.data[0] is not None

    def is_data_loading(self):
        return self._data.thread_is_running

    def set_data_label(self, new_label):
        self._data.label = new_label

    def get_data_label(self):
        return self._data.label

    def set_data_comment(self, new_comment):
        self._data.comment = new_comment

    def get_data_comment(self):
        return self._data.comment

    def calc_fitting_plane(self):
        return self._data.calc_fitting_plane()

    def get_mask_labels(self):
        return self._data.get_mask_labels()

    def get_mask_indexes(self):
        return self._data.get_mask_indexes()

    def get_circle_mask_param_labels(self):
        return self._data.get_circle_mask_param_labels()

    def get_rect_mask_param_labels(self):
        return self._data.get_rect_mask_param_labels()

    def get_range_mask_param_labels(self):
        return self._data.get_range_mask_param_labels()

    def get_x_range(self):
        return self._data.range_x

    def get_y_range(self):
        return self._data.range_y

    def get_z_range(self):
        return self._data.range_z

    def get_c_range(self):
        return self._data.range_c

    def set_step(self, new_step):
        self._data.step = new_step

    def get_step(self):
        return self._data.step

    def delete_all_masks(self):
        self._data.delete_all_masks()
        self.call_callbacks('update_data')

    def stop_loading(self):
        if self._data.thread_is_running:
            self._data.thread_is_running = False
            if self._load_file_thread is not None:
                self._load_file_thread.join()

    def load_file(self, path=None, filename=None, comment='#', separator=' ', skip_row=0):
        if path is not None:
            self.current_directory = path
        if filename is not None:
            self.current_file = filename

        if self._load_file_thread is not None:
            self._load_file_thread.join()

        self._load_file_thread = Thread(target=self._data.open_file, args=(comment, separator, skip_row,
                                                                           [lambda : self.call_callbacks(
                                                                               'update_data'),
                                                                            lambda : self.call_callbacks(
                                                                                'is_loaded')]))
        self._load_file_thread.start()

    def get_points(self):
        return self._data.data

    def add_circle_mask(self, radius=0.1, center=[0.0, 0.0, 0.0], plan='xy', is_exc=False):
        return self._data.add_circle_mask(radius, center, plan, is_exc)

    def add_rect_mask(self, low_point=[-0.1, -0.1], upper_point=[0.1, 0.1], is_exc=False):
        return self._data.add_rect_mask(low_point, upper_point, is_exc)

    def add_range_mask(self, lower=-0.1, upper=0.1, axis='x', is_exc=False):
        return self._data.add_range_mask(lower, upper, axis, is_exc)

    def set_mask_param(self, index, label, new_value):
        return self._data.set_mask_param(index, label, new_value)

    def set_mask_active(self, index, is_active):
        mask_label = self._data.get_mask_label(index)
        is_suc = self._data.set_mask_active(index, is_active)
        if is_suc:
            self._message_handler.push_message('Processor', 'info', 'New mask added, type=' + mask_label)
        return is_suc

    def get_mask_active(self, index):
        return self._data.is_mask_active(index)

    def get_mask_type(self, index):
        return self._data.get_mask_type(index)

    def get_num_masks(self):
        return self._data.n_masks

    def update_masks(self):
        self._data.update_mask(True)
        self.call_callbacks('update_data')

    def get_mask_info(self, index):
        return self._data.get_mask_info(index)

    def reset_filters(self):
        self._data.reset_filters()

    def set_use_plane(self, is_active):
        self._data.use_plane = is_active
        self._message_handler.push_message('Processor', 'info',
                                           'Using fitted plane as reference' if is_active else 'No reference plane')
        self.call_callbacks('update_data')

    def get_use_plane(self):
        return self._data.use_plane

    def get_plane(self):
        return self._data.plane
