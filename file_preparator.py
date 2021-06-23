#!/usr/bin/python
# -*- coding: utf-8 -*
__author__ = "gisly"

import os
import xml.etree.ElementTree as ET
import ffmpeg
import sys

def get_media_file_uri(src_tree):
    main_media_elements = src_tree.findall('./HEADER/MEDIA_DESCRIPTOR'
                                           '[@MIME_TYPE="audio/x-wav"]')
    if not main_media_elements:
        main_media_elements = src_tree.findall('./HEADER/MEDIA_DESCRIPTOR')
    if not main_media_elements:
        return None
    return main_media_elements[0].attrib['MEDIA_URL'].split('file:///')[-1]


def get_time_slots(src_tree):
    time_slot_elements = src_tree.findall('./TIME_ORDER/TIME_SLOT')
    time_slots = {}
    for time_slot_element in time_slot_elements:
        time_slots[time_slot_element.attrib['TIME_SLOT_ID']] = time_slot_element.attrib['TIME_VALUE']
    return time_slots


def get_aligned_sentences(src_tree, main_tier_id):
    aligned_sentence_elements = src_tree.findall('./TIER'
                                                 '[@TIER_ID="%s"]/ANNOTATION/ALIGNABLE_ANNOTATION' % main_tier_id)

    aligned_sentences = []
    for aligned_sentence_element in aligned_sentence_elements:
        aligned_sentences.append((aligned_sentence_element.attrib['TIME_SLOT_REF1'],
                                  aligned_sentence_element.attrib['TIME_SLOT_REF2'],
                                  aligned_sentence_element.find('ANNOTATION_VALUE').text))
    return aligned_sentences


def get_timelines_sentences(src_tree, main_tier_id):
    time_slots = get_time_slots(src_tree)
    aligned_sentences = get_aligned_sentences(src_tree, main_tier_id)
    return time_slots, aligned_sentences


def get_output_filename(folder_out, media_filename, ts_start, ts_end, extension):
    output_filename = os.path.basename(media_filename).split('.')[0] + \
                      '_' + ts_start + \
                      '_' + ts_end + extension
    return os.path.join(folder_out, output_filename)


def cut_media(folder_out, media_filename, time_slots, aligned_sentences):
    stream = ffmpeg.input(media_filename)
    for aligned_sentence in aligned_sentences:
        ts_start = aligned_sentence[0]
        ts_end = aligned_sentence[1]
        time_slot_start = float(time_slots[ts_start])/1000.0
        time_slot_end = float(time_slots[ts_end])/1000.0
        output_filename_full = get_output_filename(folder_out,
                                                   media_filename, ts_start, ts_end,
                                                   '.wav')
        print(output_filename_full)
        out = ffmpeg.filter(stream, 'atrim', start=time_slot_start,
                      end=time_slot_end).output(output_filename_full)
        out.run(overwrite_output=True)


def write_annotations(media_filename, aligned_sentences, folder_out):
    for aligned_sentence in aligned_sentences:
        ts_start = aligned_sentence[0]
        ts_end = aligned_sentence[1]
        sentence_text = aligned_sentence[2]
        output_filename_full = get_output_filename(folder_out,
                                                   media_filename, ts_start, ts_end,
                                                   '.txt')
        with open(output_filename_full, 'w', encoding='utf-8', newline='') as fout:
            fout.write(sentence_text)


def prepare_media_for_file(filename, folder_out, main_tier_id):
    src_tree = ET.parse(filename).getroot()
    media_file_uri = get_media_file_uri(src_tree)
    if not media_file_uri:
        print('No media for %s' % filename)
        return
    if not os.path.exists(media_file_uri):
        print('File does not exist for %s: %s' % (media_file_uri, filename))
        return
    if media_file_uri.endswith('.avi'):
        print('AVI file for %s: %s' % (media_file_uri, filename))
        return
    time_slots, aligned_sentences = get_timelines_sentences(src_tree, main_tier_id)
    cut_media(folder_out, media_file_uri, time_slots, aligned_sentences)
    write_annotations(media_file_uri, aligned_sentences, folder_out)


def prepare_media(folder_in, folder_out, main_tier_id):
    for filename in os.listdir(folder_in):
        if filename.lower().endswith('.eaf'):
            full_eaf_filename = os.path.join(folder_in, filename)
            if os.path.isfile(full_eaf_filename):
                prepare_media_for_file(full_eaf_filename, folder_out, main_tier_id)
                print('Prepared files for %s' % full_eaf_filename)


def main():
    args = sys.argv
    if len(args) < 2:
        print('usage: file_preparator eaf_folder output_folder main_tier_name')
        return
    prepare_media(args[1],
                  args[2], args[3])

if __name__ == '__main__':
    main()
    


