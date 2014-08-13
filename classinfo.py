#!/usr/bin/python
# -*-  coding:utf-8 -*-
import struct
import constant


class ClassInfo(object):
    magic = 0xCAFEBABE
    parsed = False

    def __init__(self, path):
        # self.classname = classname
        self.path = path

    # self.file = open(path,'rb')
    def __str__(self):
        if self.parsed:
            constant_list = []
            for i in xrange(1, len(self.constant_pool)):
                constant_list.append('#%-4d\t%-5s\t%s' % (i, '0x%02x' % i, self.constant_pool[i]))
            return 'version %d.%d' % (self.version[1], self.version[0]) + '\n' + \
                   'constant_pool_count = %d' % self.constant_pool_count + '\n' + \
                   'constant_pool =\n\t%s' % '\n\t'.join(constant_list) + '\n' + \
                   'flags = %s' % self.flags + '\n' + \
                   'this_class  = %s ' % self.this_class + '\n' + \
                   'super_class = %s ' % self.super_class + '\n' + \
                   'interfaces = %s ' % ','.join(self.interfaces) + '\n' + \
                   'fields = %s' % self.fields + '\n' + \
                   'methods = %s ' % self.methods + '\n' + \
                   'attributes = %s ' % self.attributes
        else:
            return super(ClassInfo, self).__str__()

    def parseStart(self):
        self.file = open(self.path, 'rb')
        return self

    def checkMagic(self):
        assert self.magic == struct.unpack('>I', self.file.read(4))[0]
        return self

    def parseVersion(self):
        version_raw = self.file.read(4)
        self.version = struct.unpack('>HH', version_raw)
        return self

    def parseConstantInfo(self):
        constant_pool_count = struct.unpack('>H', self.file.read(2))[0]
        self.constant_pool_count = constant_pool_count - 1
        for i in xrange(1, constant_pool_count):
            tag = struct.unpack('>B', self.file.read(1))[0]
            constantInfo = constant.Constants.createConstant(tag, [self.file.read(step) for step in
                                                                   constant.Constants.nextStep(tag)])
            if isinstance(constantInfo, constant.ConstantUtf8):
                constantInfo.parseStringValue(self.file.read(constantInfo.length))
        constant.Constants.indexToValue()
        self.constant_pool = constant.Constants.constant_pool
        return self

    def parseAccessFlag(self):
        flag = struct.unpack('>H', self.file.read(2))[0]
        self.flags = access_flag_to_string(flag)
        return self

    def parseThisClass(self):
        self.this_class_index = this_class_index = struct.unpack('>H', self.file.read(2))[0]
        this_class_info = self.constant_pool[this_class_index]
        assert isinstance(this_class_info, constant.ConstantClassref)
        self.this_class = this_class_info.value
        return self

    def parseSuperClass(self):
        self.super_class_index = super_class_index = struct.unpack('>H', self.file.read(2))[0]
        super_class_info = self.constant_pool[super_class_index]
        assert isinstance(super_class_info, constant.ConstantClassref)
        self.super_class = super_class_info.value
        return self

    def parseInterfaces(self):
        self.interfaces_count = interfaces_count = struct.unpack('>H', self.file.read(2))[0]
        self.interfaces = []
        for i in xrange(interfaces_count):
            interface_index = struct.unpack('>H', self.file.read(2))[0]
            interface_info = self.constant_pool[interface_index]
            assert isinstance(interface_info, constant.ConstantClassref)
            self.interfaces.append(interface_info.value)
        return self

    def parseFields(self):
        self.fields_count = fields_count = struct.unpack('>H', self.file.read(2))[0]
        self.fields = []
        for i in xrange(fields_count):
            field = {}
            access_flag = struct.unpack('>H', self.file.read(2))[0]
            field['access_flag'] = access_flag_to_string(access_flag)
            name_index = struct.unpack('>H', self.file.read(2))[0]
            name_utf8 = self.constant_pool[name_index]
            assert isinstance(name_utf8, constant.ConstantUtf8)
            field['name'] = name_utf8.value
            descriptor_index = struct.unpack('>H', self.file.read(2))[0]
            descriptor_utf8 = self.constant_pool[descriptor_index]
            assert isinstance(descriptor_utf8, constant.ConstantUtf8)
            field['descriptor'] = descriptor_utf8.value
            attribute_count = struct.unpack('>H', self.file.read(2))[0]
            if attribute_count and attribute_count > 0:
                field['attributes'] = self._get_attributes(attribute_count)
            self.fields.append(field)
        return self

    def parseMethods(self):
        self.methods_count = methods_count = struct.unpack('>H', self.file.read(2))[0]
        self.methods = []
        for i in xrange(methods_count):
            method = {}
            access_flag = struct.unpack('>H', self.file.read(2))[0]
            method['access_flag'] = access_flag_to_string(access_flag)
            name_index = struct.unpack('>H', self.file.read(2))[0]
            name_utf8 = self.constant_pool[name_index]
            assert isinstance(name_utf8, constant.ConstantUtf8)
            method['name'] = name_utf8.value
            descriptor_index = struct.unpack('>H', self.file.read(2))[0]
            descriptor_utf8 = self.constant_pool[descriptor_index]
            assert isinstance(descriptor_utf8, constant.ConstantUtf8)
            method['descriptor'] = descriptor_utf8.value
            attribute_count = struct.unpack('>H', self.file.read(2))[0]
            if attribute_count and attribute_count > 0:
                method['attributes'] = self._get_attributes(attribute_count)
            self.methods.append(method)
        return self

    def parseAttributes(self):
        self.attributes_count = attributes_count = struct.unpack('>H', self.file.read(2))[0]
        self.attributes = self._get_attributes(attributes_count)
        return self

    def parseEnd(self):
        self.file.close()

    def parse(self):
        self.parseStart().checkMagic().parseVersion().parseConstantInfo(). \
            parseAccessFlag().parseThisClass().parseSuperClass().parseInterfaces(). \
            parseFields().parseMethods().parseAttributes().parseEnd()
        self.parsed = True

    def _get_attributes(self, attribute_count, parse_attribute_value=False):
        attributes = []
        if attribute_count and attribute_count > 0:
            for j in xrange(attribute_count):
                attribute = {}
                attribute_name_index = struct.unpack('>H', self.file.read(2))[0]
                attribute_name_utf8 = self.constant_pool[attribute_name_index]
                assert isinstance(attribute_name_utf8, constant.Constant)
                attribute['name'] = attribute_name_utf8.value
                is_code_attribute = isinstance(attribute['name'], str) and attribute['name'].lower() == 'code'
                is_bootstrap_methods = isinstance(attribute['name'], str) and attribute[
                                                                                  'name'].lower() == 'bootstrapmethods'
                is_inner_classes = isinstance(attribute['name'], str) and attribute['name'].lower() == 'innerclasses'
                data_length = struct.unpack('>I', self.file.read(4))[0]
                raw_value = self.file.read(data_length)
                if not (is_code_attribute and is_bootstrap_methods and is_inner_classes) and data_length == 2:
                    constant_value_index = struct.unpack('>H', raw_value)[0]
                    constant_value_ref = self.constant_pool[constant_value_index]
                    if isinstance(constant_value_ref, constant.ConstantInteger) or \
                            isinstance(constant_value_ref, constant.ConstantFloat) or \
                            isinstance(constant_value_ref, constant.ConstantDouble) or \
                            isinstance(constant_value_ref, constant.ConstantLong) or \
                            isinstance(constant_value_ref, constant.ConstantString):
                        attribute['value'] = constant_value_ref.value
                elif is_code_attribute:
                    if parse_attribute_value:
                        attribute['value'] = self._parse_code(raw_value)
                    else:
                        attribute['value'] = format_raw(raw_value)
                elif is_bootstrap_methods:
                    attribute['value'] = self._parse_bootstrap_methods(raw_value)
                elif is_inner_classes:
                    attribute['value'] = self._parse_inner_classes(raw_value)
                else:
                    attribute['value'] = format_raw(raw_value)
                attributes.append(attribute)
        return attributes

    #unusefull some eror
    def _parse_code(self, raw_data):
        value = {}
        value['max_stack'] = struct.unpack('>H', raw_data[:2])[0]
        value['max_locals'] = struct.unpack('>H', raw_data[2:4])[0]
        value['code_length'] = struct.unpack('>I', raw_data[4:8])[0]
        value['codes'] = []
        for i in xrange(value['code_length']):
            byte = raw_data[8 + i]
            value['codes'].append(byte)
        cur = 8 + value['code_length']
        value['exception_table_length'] = struct.unpack('>H', raw_data[cur:cur + 2])[0]
        cur = cur + 2
        value['exception_table'] = []
        for i in xrange(value['exception_table_length']):
            exception_table = {}
            exception_table['start_pc'] = struct.unpack('>H', raw_data[(cur + i * 8):(cur + i * 8 + 2)])[0]
            exception_table['end_pc'] = struct.unpack('>H', raw_data[(cur + i * 8 + 2):(cur + i * 8 + 4)])[0]
            exception_table['handler_pc'] = struct.unpack('>H', raw_data[(cur + i * 8 + 4):(cur + i * 8 + 6)])[0]
            exception_table['catch_type'] = struct.unpack('>H', raw_data[(cur + i * 8 + 6):(cur + i * 8 + 8)])[0]
            value['exception_table'].append(exception_table)
        cur = cur + value['exception_table_length'] * 8
        value['attribute_count'] = struct.unpack('>H', raw_data[cur:cur + 2])[0]
        value['attributes'] = self._get_attributes(value['attribute_count'])
        return value

    def _parse_bootstrap_methods(self, raw_data):
        value = []
        bootstrap_methods_count = struct.unpack('>H', raw_data[:2])[0]
        cur = 2
        for i in xrange(bootstrap_methods_count):
            bootstrap_method = {}
            name_index = struct.unpack('>H', raw_data[cur:cur + 2])[0]
            name_ref = self.constant_pool[name_index]
            assert isinstance(name_ref, constant.ConstantMethodHandle)
            bootstrap_method['name'] = name_ref.value
            cur += 2
            bootstrap_method['args'] = []
            args_length = struct.unpack('>H', raw_data[cur:cur + 2])[0]
            cur += 2
            for j in xrange(args_length):
                arg_index = struct.unpack('>H', raw_data[cur:cur + 2])[0]
                arg_ref = self.constant_pool[arg_index]
                assert isinstance(arg_ref, constant.ConstantMethodType) or isinstance(arg_ref,
                                                                                      constant.ConstantMethodHandle)
                bootstrap_method['args'].append(arg_ref.value)
                cur += 2
            value.append(bootstrap_method)
        return value

    def _parse_inner_classes(self, raw_data):
        value = []
        inner_classes_count = struct.unpack('>H', raw_data[:2])[0]
        cur = 2
        for i in xrange(inner_classes_count):
            inner_class = {}
            class_ref_index = struct.unpack('>H', raw_data[cur:cur + 2])[0]
            class_ref = self.constant_pool[class_ref_index]
            assert isinstance(class_ref, constant.ConstantClassref)
            inner_class['class'] = class_ref.value
            cur += 2
            parent_class_ref_index = struct.unpack('>H', raw_data[cur:cur + 2])[0]
            parent_class_ref = self.constant_pool[parent_class_ref_index]
            assert isinstance(parent_class_ref, constant.ConstantClassref)
            inner_class['parent_class'] = parent_class_ref.value
            cur += 2
            name_index = struct.unpack('>H', raw_data[cur:cur + 2])[0]
            name_ref = self.constant_pool[name_index]
            assert isinstance(name_ref, constant.ConstantUtf8)
            inner_class['name'] = name_ref.value
            cur += 2
            access_flag =struct.unpack('>H', raw_data[cur:cur+2])[0]
            inner_class['access_flag'] = access_flag_to_string(access_flag)
            cur += 2
            value.append(inner_class)
        return value


def format_raw(raw_data):
    data_length = len(raw_data)
    tuple_value = struct.unpack('>' + 'B' * data_length, raw_data)
    str_value = '\\x%02x' * data_length % tuple_value
    return str_value

def access_flag_to_string(flag):
    flag_info = []
    if flag & 0x0001:
        flag_info.append('ACC_PUBLIC')
    if flag & 0x0002:
        flag_info.append('ACC_PRIVATE')
    if flag & 0x0004:
        flag_info.append('ACC_PROTECTED')
    if flag & 0x0008:
        flag_info.append('ACC_STATIC')
    if flag & 0x0010:
        flag_info.append('ACC_FINAL')
    if flag & 0x0020:
        flag_info.append('ACC_SUPER')
    if flag & 0x0040:
        flag_info.append('ACC_VOILATIE')
    if flag & 0x0080:
        flag_info.append('ACC_TRANSIENT')
    if flag & 0x0100:
        flag_info.append('ACC_NATIVE')
    if flag & 0x0200:
        flag_info.append('ACC_INTERFACE')
    if flag & 0x0400:
        flag_info.append('ACC_ABSTRACT')
    if flag & 0x1000:
        flag_info.append('ACC_SYNTHETIC')
    if flag & 0x2000:
        flag_info.append('ACC_ANNOTATION')
    if flag & 0x4000:
        flag_info.append('ACC_ENUM')
    return '|'.join(flag_info)

if __name__ == '__main__':
    clzz = ClassInfo(r'E:\jee\workspace\test\bin\test\TTest.class')
    clzz.parse()
    print '%s' % clzz
