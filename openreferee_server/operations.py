import io
import tempfile
from collections import defaultdict
from pathlib import Path
from urllib.request import urlopen, Request

import requests
from PyPDF2 import PdfFileWriter, PdfFileReader
from flask import current_app

from .defaults import DEFAULT_EDITABLES, DEFAULT_FILE_TYPES, DEFAULT_TAGS


def setup_requests_session(token):
    session = requests.Session()
    session.headers = {"Authorization": "Bearer {}".format(token)}
    if current_app.debug:
        session.verify = False
    return session


def get_event_tags(session, event):
    tag_endpoint = event.endpoints["tags"]["list"]

    current_app.logger.info("Fetching available tags...")
    response = session.get(tag_endpoint)
    response.raise_for_status()
    return {t["code"]: t for t in response.json()}


def setup_event_tags(session, event):
    tag_endpoint = event.endpoints["tags"]["create"]
    available_tags = get_event_tags(session, event)

    current_app.logger.info("Adding missing tags...")
    for code, data in DEFAULT_TAGS.items():
        if code in available_tags:
            # tag already available in Indico event
            continue
        response = session.post(tag_endpoint, json=dict(data, code=code))
        response.raise_for_status()
        current_app.logger.info("Added '{}'...".format(code))


def cleanup_event_tags(session, event):
    available_tags = get_event_tags(session, event)
    for tag_name in DEFAULT_TAGS:
        if tag_name not in available_tags:
            continue
        tag = available_tags[tag_name]
        if not tag["is_used_in_revision"]:
            # delete tag, as it's unused
            response = session.delete(tag["url"])
            response.raise_for_status()
            current_app.logger.info("Deleted tag '{}'".format(tag["title"]))


def get_file_types(session, event, editable):
    endpoint = event.endpoints["file_types"][editable]["list"]
    current_app.logger.info("Fetching available file types ({})...".format(editable))
    response = session.get(endpoint)
    response.raise_for_status()
    return {t["name"]: t for t in response.json()}


def setup_file_types(session, event):
    for editable in DEFAULT_EDITABLES:
        available_file_types = get_file_types(session, event, editable)
        for type_data in DEFAULT_FILE_TYPES[editable]:
            if type_data["name"] in available_file_types:
                continue
            endpoint = event.endpoints["file_types"][editable]["create"]
            response = session.post(endpoint, json=type_data)
            response.raise_for_status()
            current_app.logger.info(
                "Added '{}' to '{}'".format(type_data["name"], type_data)
            )


def cleanup_file_types(session, event):
    for editable in DEFAULT_EDITABLES:
        available_types = get_file_types(session, event, editable)
        for ftype in DEFAULT_FILE_TYPES[editable]:
            server_type = available_types[ftype["name"]]
            if not server_type["is_used_in_condition"] and not server_type["is_used"]:
                response = session.delete(server_type["url"])
                response.raise_for_status()
                current_app.logger.info(
                    "Deleted file type '{}'".format(server_type["name"])
                )


def cleanup_event(event):
    session = setup_requests_session(event.token)
    cleanup_event_tags(session, event)
    cleanup_file_types(session, event)


def process_editable_files(session, files, endpoints):
    uploaded = defaultdict(list)
    for _file in files:
        if _file['filename'].split(".")[-1] == 'pdf':
            upload = process_pdf(_file['external_download_url'], session, endpoints['file_upload'])
            uploaded[_file['file_type']].append(upload['uuid'])
    session.post(endpoints['revisions']['replace'], json={
        'files': uploaded,
        'state': 'ready_for_review'
    })


def process_pdf(url, session, upload_endpoint):
    pdf_writer = PdfFileWriter()
    rf = urlopen(Request(url, headers=session.headers))
    pdf_reader = PdfFileReader(io.BytesIO(rf.read()))
    watermark_pdf = PdfFileReader(open(Path(__file__).parent / 'watermark.pdf', 'rb'))
    watermark_page = watermark_pdf.getPage(0)
    for page in range(0, pdf_reader.numPages):
        page = pdf_reader.getPage(0)
        page.mergePage(watermark_page)
        pdf_writer.addPage(page)
    with tempfile.NamedTemporaryFile(suffix='.pdf') as f:
        pdf_writer.write(f)
        f.seek(0)
        r = session.post(upload_endpoint, files={'file': f})
        return r.json()
