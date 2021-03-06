from rest_framework import serializers
from formshare.apps.logger.models.attachment import Attachment
from formshare.libs.utils.decorators import check_obj
from formshare.libs.utils.image_tools import image_url
import json


def dict_key_for_value(_dict, value):
    """
    This function is used to get key by value in a dictionary
    """
    return _dict.keys()[_dict.values().index(value)]


def get_path(data, question_name, path_list):
    """
    A recursive function that returns the xpath of a media file
    :param json data: JSON representation of xform
    :param string question_name: Name of media file being searched for
    :param list path_list: Contains the names that make up the xpath
    :return: an xpath which is a string or None if name cannot be found
    :rtype: string or None
    """
    name = data.get('name')
    if name == question_name:
        return '/'.join(path_list)
    elif data.get('children') is not None:
        for node in data.get('children'):
            path_list.append(node.get('name'))
            path = get_path(node, question_name, path_list)
            if path is not None:
                return path
            else:
                del path_list[len(path_list) - 1]
    return None


class AttachmentSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='attachment-detail',
                                               lookup_field='pk')
    field_xpath = serializers.SerializerMethodField('get_field_xpath')
    download_url = serializers.SerializerMethodField('get_download_url')
    small_download_url = serializers.SerializerMethodField(
        'get_small_download_url')
    medium_download_url = serializers.SerializerMethodField(
        'get_medium_download_url')
    xform = serializers.Field(source='instance.xform.pk')
    instance = serializers.Field(source='instance.pk')
    filename = serializers.Field(source='media_file.name')

    class Meta:
        fields = ('url', 'filename', 'mimetype', 'field_xpath', 'id', 'xform',
                  'instance', 'download_url', 'small_download_url',
                  'medium_download_url')
        lookup_field = 'pk'
        model = Attachment

    @check_obj
    def get_download_url(self, obj):
        return obj.media_file.url if obj.media_file.url else None

    def get_small_download_url(self, obj):
        if obj.mimetype.startswith('image'):
            return image_url(obj, 'small')

    def get_medium_download_url(self, obj):
        if obj.mimetype.startswith('image'):
            return image_url(obj, 'medium')

    def get_field_xpath(self, obj):
        qa_dict = obj.instance.get_dict()
        if obj.filename not in qa_dict.values():
            return None

        question_name = dict_key_for_value(qa_dict, obj.filename)
        data = json.loads(obj.instance.xform.json)

        return get_path(data, question_name, [])
