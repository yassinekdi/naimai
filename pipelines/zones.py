import os
from naimai.constants.paths import path_dispatched, path_formatted, path_produced
import shutil

class Zone:
    def __init__(self, zone_path, zone_name):
        self.elements = {}
        self.zone_path = zone_path
        self.zone_name = zone_name

    def get_elements(self):
        if self.zone_path:
            elements = os.listdir(self.zone_path)
            for elt in elements:
                path_elt = os.path.join(self.zone_path, elt)
                if os.path.isdir(path_elt):
                    self.elements[elt] = os.listdir(path_elt)
                else:
                    self.elements[elt] = ''

    def create_fields(self, fields_names):
        for field in fields_names:
            path = os.path.join(self.zone_path, field)
            os.mkdir(path)

    def reset_all(self):
        '''
        clear the zone
        :return:
        '''
        elements = os.listdir(self.zone_path)
        for elt in elements:
            path = os.path.join(self.zone_path, elt)
            if os.path.isdir(path):
                os.rmdir(path)
            else:
                os.remove(path)

    def reset_all_elements(self):
        '''
        clear all elements (folders) of the zone
        :return:
        '''
        for element in self.elements:
            self.reset_element(element)

    def reset_element(self, element):
        '''
        clear the elements of the input element (field/folder)
        :param element: field/folder of the zone
        :return:
        '''
        if element in self.elements:
            path_element = os.path.join(self.zone_path, element)
            if os.path.isdir(path_element):
                files = os.listdir(path_element)
                for f in files:
                    path = os.path.join(path_element, f)
                    if os.path.isfile(path):
                        os.remove(path)
                    elif os.path.isdir(path):
                        shutil.rmtree(path)
            else:
                print('{} is not a directory'.format(element))
        else:
            print('{} is not an element in {} zone'.format(element, self.zone_name))


class Dispatched_Zone(Zone):
    def __init__(self):
        super().__init__(zone_path=path_dispatched, zone_name='dispatched')
        self.get_elements()


class Formatted_Zone(Zone):
    def __init__(self):
        super().__init__(zone_path=path_formatted, zone_name='formatted')
        self.get_elements()


class Production_Zone(Zone):
    def __init__(self):
        super().__init__(zone_path=path_produced, zone_name='production')
        self.get_elements()


