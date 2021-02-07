import re
from collections import deque
from dataclasses import dataclass, field, replace
from typing import Type

import numpy as np
import pandas as pd
import copy


# little helper class
class ldf_dict(dict):
    def __init__(self):
        self = dict()

    def add(self, key, value):
        self[key] = value

@dataclass
class Nodes:
    master: str
    timer_base_ms: float
    jitter_ms: float
    slaves: list = field(default_factory=list)

@dataclass(init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=False)
class Signal:
    size: int
    init_val: int
    publisher: str
    subscriber: str

@dataclass(init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=False)
class Frame:
    identifier: int
    publisher: str
    response_length: int
    signals: ldf_dict()

@dataclass(init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=False)
class Diagnostic_signal:
    size: int
    init_val: int

@dataclass
class Node_attribute:
    lin_protocol: float
    configure_NAD: str
    product_id: list
    response_error: str
    P2_min_ms: int
    ST_min_ms: int
    configure_frames: ldf_dict()


class LDFParser:
    """
    Wording: every element of the ldf e.g. Nodes {} or Signals {} is
    called attribute.
    """
    __closed_curly: np.ndarray
    __opened_curly: np.ndarray
    __ldf_data: np.ndarray
    __start_of_attribute: np.ndarray
    __start_of_frames: np.ndarray

    # frames: key=frame_name, value=frame data
    frames = ldf_dict()
    node_attributes = ldf_dict()
    schedule_tables = ldf_dict()
    signals = ldf_dict()
    diagnostic_signals = ldf_dict()
    signal_encoding_types = ldf_dict()
    signal_representation = ldf_dict()
    nodes = Nodes

    def __init__(self, ldf_path):
        self.__ldf_data = pd.read_csv(ldf_path, sep="\n", encoding='latin-1')
        self.__ldf_data = self.__ldf_data.values
        self.__remove_header_info()
        self.__analyse_ldf_elements()

    def parse_all(self):
        for (line_number, axis), value in np.ndenumerate(self.__start_of_attribute):
            if value and self.__ldf_data[line_number]   == "Nodes {":
                self.get_nodes(line_number)
            elif value and self.__ldf_data[line_number] == "Signals {":
                self.get_signals(line_number)
            elif value and self.__ldf_data[line_number] == "Diagnostic_signals {":
                self.get_dignostic_signals(line_number)
            elif value and self.__ldf_data[line_number] == "Frames {":
                self.get_frames()
            elif value and self.__ldf_data[line_number] == "Node_attributes {":
                self.get_node_attributes(line_number)
            elif value and self.__ldf_data[line_number] == "Schedule_tables {":
                self.get_schedule_table(line_number)
            elif value and self.__ldf_data[line_number] == "Signal_encoding_types {":
                self.get_signal_encoding_types(line_number)
            elif value and self.__ldf_data[line_number] == "Signal_representation {":
                self.get_signal_representation(line_number)
        del self.__ldf_data, self.__closed_curly, self.__start_of_frames, self.__start_of_attribute

    def get_nodes(self, line_number=-1):
        nodes = Nodes
        if line_number == -1:
            line_number = int(np.where(self.__ldf_data == "Nodes {")[0]) + 1
        end_of_nodes = self.__get_index_of_next_closed_curly(line_number)
        while line_number < end_of_nodes:
            line_number = line_number + 1
            current_line_value = self.__ldf_data[line_number][0]
            current_line_value = self.__remove_unwanted(current_line_value).split(':')
            if current_line_value[0] == "Master":
                master_values = current_line_value[1].split(',')
                nodes.master = master_values[0]
                nodes.timer_base_ms = float(self.__remove_all_but_num(master_values[1]))
                nodes.jitter_ms = float(self.__remove_all_but_num(master_values[2]))
            elif current_line_value[0] == "Slaves":
                nodes.slaves = current_line_value[1].split(',')
        self.nodes = nodes

    def get_frames(self):
        # self.start_of_frame contains all starting positons of the frame elements
        start_frame_indizes = np.where(self.__start_of_frames[:, 0])[0]
        end_frame_indizes = np.where(self.__closed_curly[:, 0])[0]
        end_frame_indizes = deque(end_frame_indizes)
        # remove not needed closing curly braces
        while end_frame_indizes[0] < start_frame_indizes[0]:
            end_frame_indizes.popleft()
        end_frames_index = self.__get_end_of_attribute(start_frame_indizes[0])
        start_frame_indizes = deque(start_frame_indizes)
        current_line_number = start_frame_indizes.popleft()
        while current_line_number < end_frames_index:
            # first parse the frame header ..
            frame = Frame(identifier=0, publisher="", response_length=0, signals=ldf_dict())
            frame_header = self.__raw_line_to_list(self.__ldf_data[current_line_number][0])
            frame.identifier = frame_header[1]
            frame.publisher = frame_header[2]
            frame.response_length = int(frame_header[3])
            current_line_number = current_line_number + 1
            # .. and then the signals
            end_of_frame_signals = self.__get_end_of_attribute(current_line_number, 1)
            signals = ldf_dict()
            while current_line_number < end_of_frame_signals:
                signal = ldf_dict()
                signal_line = self.__remove_unwanted(self.__ldf_data[current_line_number][0]).split(",")
                signal_name = signal_line[0]
                signal_offset = signal_line[1]
                signal.add("Offset", signal_offset)
                signals.add(signal_name, signal)
                current_line_number = current_line_number + 1
            frame.signals = signals
            self.frames.add(frame_header[0], frame)
            current_line_number = current_line_number + 1

    def get_node_attributes(self, line_number):
        end_of_node_attr = self.__get_end_of_attribute(line_number, 3)
        line_number = line_number + 1
        while line_number < end_of_node_attr:
            node_attribute = Node_attribute(lin_protocol=0.0, configure_NAD="", product_id=[], response_error="",
                                            P2_min_ms=0, ST_min_ms=0, configure_frames=ldf_dict())
            node_attribute_name = self.__remove_unwanted(self.__ldf_data[line_number][0])
            line_number = line_number + 1
            node_attribute.lin_protocol = float(self.__remove_unwanted(self.__ldf_data[line_number][0]).split("=")[1])
            line_number = line_number + 1
            node_attribute.configure_NAD = self.__remove_unwanted(self.__ldf_data[line_number][0]).split("=")[1]
            line_number = line_number + 1
            node_attribute.product_id = self.__remove_unwanted(self.__ldf_data[line_number][0]).split("=")[1].split(",")
            line_number = line_number + 1
            node_attribute.response_error = self.__remove_unwanted(self.__ldf_data[line_number][0]).split("=")[1]
            line_number = line_number + 1
            node_attribute.P2_min_ms = int(re.sub(r'[^0-9]', '', self.__remove_unwanted(self.__ldf_data[line_number][0]).split("=")[1]))
            line_number = line_number + 1
            node_attribute.ST_min_ms = int(re.sub(r'[^0-9]', '', self.__remove_unwanted(self.__ldf_data[line_number][0]).split("=")[1]))
            line_number = line_number + 2
            end_of_configurable_frames = self.__get_end_of_attribute(line_number, 1)
            conf_frame_dict = ldf_dict()
            while line_number < end_of_configurable_frames:
                conf_frame = self.__remove_unwanted(self.__ldf_data[line_number][0]).split("=")
                conf_frame_dict.add(conf_frame[0], conf_frame[1])
                line_number = line_number + 1
            node_attribute.configure_frames = conf_frame_dict
            self.node_attributes.add(node_attribute_name, node_attribute)
            line_number = self.__get_end_of_attribute(line_number, 2) + 2

    def get_signal_representation(self, current_line_number):
        current_line_number = current_line_number + 1
        end_of_signal_representation = self.__get_index_of_next_closed_curly(current_line_number)
        while current_line_number < end_of_signal_representation:
            signal_representation_list = self.__remove_unwanted(self.__ldf_data[current_line_number][0]).split(":")
            signal_repre_key = signal_representation_list[0]
            signal_repre_val = signal_representation_list[1].split(",")
            current_line_number = current_line_number + 1
            self.signal_representation.add(signal_repre_key, signal_repre_val)

    def get_signal_encoding_types(self, current_line_number):
        current_line_number = current_line_number + 1
        end_of_signal_enc_types = self.__get_end_of_attribute(current_line_number, 2)
        while current_line_number < end_of_signal_enc_types:
            signal_encoding_name = self.__remove_unwanted(self.__ldf_data[current_line_number][0])
            current_line_number = current_line_number + 1
            end_of_current_sign_enc_type = self.__get_index_of_next_closed_curly(current_line_number)
            encoding_list = []
            while current_line_number < end_of_current_sign_enc_type:
                val_list = self.__ldf_data[current_line_number][0].split(",")
                for i in range(0, len(val_list)):
                    val_list[i] = re.sub(r"^[\s]*|[\";]", "", val_list[i])
                encoding_list.append(val_list)
                current_line_number = current_line_number + 1
            self.signal_encoding_types.add(signal_encoding_name, encoding_list)
            current_line_number = current_line_number + 1

    def get_schedule_table(self, current_line_number):
        current_line_number = current_line_number + 1
        end_of_schedule_tables = self.__get_end_of_attribute(current_line_number, 2)
        while current_line_number < end_of_schedule_tables:
            schedule_table_name = self.__remove_unwanted(self.__ldf_data[current_line_number][0])
            current_line_number = current_line_number + 1
            end_of_current_schedule_table = self.__get_index_of_next_closed_curly(current_line_number)
            frame_slots = ldf_dict()
            while current_line_number < end_of_current_schedule_table:
                #schedule_table = Schedule_table(frame_slot_name="", frame_slot_duration_ms=0)
                current_line_list = re.sub(r"[\t]", "", self.__ldf_data[current_line_number][0]).split(" ")
                frame_slot_name = current_line_list[0]
                frame_slot_duration_ms = current_line_list[2]
                frame_slots.add(frame_slot_name, int(frame_slot_duration_ms))
                current_line_number = current_line_number + 1
            self.schedule_tables.add(schedule_table_name, frame_slots)
            current_line_number = current_line_number + 1

    def get_signals(self, current_line_number):
        current_line_number = current_line_number + 1
        end_of_signals = self.__get_index_of_next_closed_curly(current_line_number)
        while current_line_number < end_of_signals:
            signal = Signal(size=0, init_val=0, publisher="", subscriber="")
            raw_line = self.__ldf_data[current_line_number][0]
            line_as_list = self.__raw_line_to_list(raw_line)
            signal.size = line_as_list[1]
            signal.init_val = line_as_list[2]
            signal.publisher = line_as_list[3]
            signal.subscriber = line_as_list[4]
            current_line_number = current_line_number + 1
            self.signals.add(line_as_list[0], signal)

    def get_dignostic_signals(self, current_line_number):
        current_line_number = current_line_number + 1
        end_of_diagnostic_signals = self.__get_index_of_next_closed_curly(current_line_number)
        while current_line_number < end_of_diagnostic_signals:
            diagnostic_signal = Diagnostic_signal(size=0, init_val=0)
            raw_line = self.__ldf_data[current_line_number][0]
            line_as_list = self.__raw_line_to_list(raw_line)
            diagnostic_signal.size = line_as_list[1]
            diagnostic_signal.init_val = line_as_list[2]
            self.diagnostic_signals.add(line_as_list[0], diagnostic_signal)
            current_line_number = current_line_number + 1

    def __remove_unwanted(self, string: str) -> str:
        """
        :param string: string that contains commas, semicols, whitespace, tabspace or closed curly
        :return: cleaned string
        """
        return re.sub(r'[\s\t;{}"]*', '', string, flags=re.M)

    def __analyse_ldf_elements(self):
        # TODO: optimzable since it runs three times over the file
        start_pattern = re.compile(r'\b\w+\s{$')
        start_vmatch = np.vectorize(lambda x: bool(start_pattern.match(x)))
        self.__start_of_attribute = start_vmatch(self.__ldf_data)

        # find all closed curlys
        close_curly_pattern = re.compile(r'\s*}$')
        end_vmatch = np.vectorize(lambda x: bool(close_curly_pattern.match(x)))
        self.__closed_curly = end_vmatch(self.__ldf_data)

        open_curly_pattern = re.compile(r'.*{$')
        open_curly_vmatch = np.vectorize(lambda x: bool(open_curly_pattern.match(x)))
        self.__opened_curly = open_curly_vmatch(self.__ldf_data)

        frames_pattern = re.compile(r'\s*[A-Za-z0-9_]+:[\d\sA-Za-z,_]+{$')
        # example: 	AQSe_01: 10, Klima_LIN1, 6 {
        frames_vmatch = np.vectorize(lambda x: bool(frames_pattern.match(x)))
        self.__start_of_frames = frames_vmatch(self.__ldf_data)

    def __remove_all_but_num(self, string: str) -> str:
        return  re.sub(r'[^0-9.]', '', string, flags=re.M)

    def __raw_line_to_list(self, line):
        line = self.__remove_unwanted(line).split(":")
        line = line[:1] + line[1].split(",")
        return line

    def __remove_header_info(self):
        counter = 0
        for line in self.__ldf_data:
            if "/*" in line[0]:
                counter = counter + 1
        if counter != 0:
            self.__ldf_data = self.__ldf_data[counter:]

    def __get_index_of_next_closed_curly(self, index):
        index_ = index + 1
        while not self.__closed_curly[index_]:
            index_ = index_ + 1
        return index_

    def __write_to_arr_till_closed_curly(self, index, np_arr):
        index_ = index + 1
        while not self.__closed_curly[index_]:
            np_arr = np.append(np_arr, self.__ldf_data[index_][0])
            index_ = index_ + 1
        return np_arr

    def __get_end_of_attribute(self, index, successive_closed_curly=2):
        # find end of block by double or tripple closed curly braces
        i = index
        if successive_closed_curly == 1:
            while not self.__closed_curly[i]:
                i = i + 1
        elif successive_closed_curly == 2:
            while not self.__closed_curly[i] or not self.__closed_curly[i + 1]:
                i = i + 1
        elif successive_closed_curly == 3:
            while not self.__closed_curly[i] or not self.__closed_curly[i + 1] or not self.__closed_curly[i + 2]:
                i = i + 1
        else:
            print("Number of curly not supported")
        return i
