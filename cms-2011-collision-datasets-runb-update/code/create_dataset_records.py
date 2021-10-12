#!/usr/bin/env python
# noqa: E501

"""
Create CMS 2011 RunB open data release collision datasets.
"""

import click
import csv
import hashlib
import json
import os
import re
import subprocess

from create_eos_file_indexes import (
    XROOTD_URI_BASE,
    get_dataset_index_file_base,
    get_dataset_location,
)

FWYZARD = {}

FILEINFO = {}

CMS_2011_RUNA_CONFIG_RECORDS_LINK_INFO = {}
exec(open("./inputs/cms_2011_runa_config_records.py", "r").read())

DOI_INFO = {}


def get_from_deep_json(data, akey):
    "Traverse DATA and return first value matching AKEY."
    if type(data) is dict:
        if akey in data.keys():
            return data[akey]
        else:
            for val in data.values():
                if type(val) is dict:
                    aval = get_from_deep_json(val, akey)
                    if aval:
                        return aval
                if type(val) is list:
                    for elem in val:
                        aval = get_from_deep_json(elem, akey)
                        if aval:
                            return aval
    if type(data) is list:
        for elem in data:
            aval = get_from_deep_json(elem, akey)
            if aval:
                return aval
    return None


def get_das_store_json(dataset):
    "Return DAS JSON from the DAS JSON Store for the given dataset."
    filepath = "./inputs/das-json-store/" + dataset.replace("/", "@") + ".json"
    with open(filepath, "r") as filestream:
        return json.load(filestream)


def get_number_events(dataset):
    """Return number of events for the dataset."""
    number_events = get_from_deep_json(get_das_store_json(dataset), "nevents")
    if number_events:
        return number_events
    return 0


def get_number_files(dataset):
    """Return number of files for the dataset."""
    number_files = get_from_deep_json(get_das_store_json(dataset), "nfiles")
    if number_files:
        return number_files
    return 0


def get_size(dataset):
    """Return size of the dataset."""
    size = get_from_deep_json(get_das_store_json(dataset), "size")
    if size:
        return size
    return 0


def get_file_size(afile):
    "Return file size of a file."
    return os.path.getsize(afile)


def get_file_checksum(afile):
    """Return the SHA1 checksum of a file."""
    return hashlib.sha1(open(afile, "rb").read()).hexdigest()


def populate_fwyzard():
    """Populate FWYZARD dictionary (dataset -> trigger list)."""
    for line in open("./inputs/fwyzard-hlt-2011-dataset.txt", "r").readlines():
        dataset, trigger = line.split()
        if dataset in FWYZARD.keys():
            FWYZARD[dataset].append(trigger)
        else:
            FWYZARD[dataset] = [
                trigger,
            ]


def populate_doiinfo():
    """Populate DOI_INFO dictionary (dataset -> doi)."""
    for line in open("./inputs/dois.txt", "r").readlines():
        dataset, doi = line.split()
        DOI_INFO[dataset] = doi


def populate_fileinfo():
    """Populate FILEINFO dictionary (file -> size)."""
    return
    for line in open("./inputs/eos-file-information.txt", "r").readlines():
        match = re.search(r"^path=(.*) size=(.*)$", line)
        if match:
            file_path, file_size = match.groups()
            if file_path in FILEINFO:
                raise Exception("Multiple FILEINFO files %s." % file_path)
            else:
                FILEINFO[file_path] = int(file_size)


def create_selection_information(dataset, dataset_full_name):
    """Create box with selection information."""
    out = ""
    out += "</p>"
    # data taking / HLT:
    out += "<p><strong>Data taking / HLT</strong>"
    out += '<br/>The collision data were assigned to different RAW datasets using the following <a href="/record/1701">HLT configuration</a>.</p>'
    # data processing / RECO:
    run_period = re.search(r"(Run[0-9]+.)", dataset_full_name).groups()[0]
    afile = "reco_" + run_period[3:-1] + "A_" + dataset
    process = "RECO"
    generator_text = "Configuration file for " + process + " step " + afile
    release = "CMSSW_5_3_7_patch5"
    global_tag = "FT_R_53_V18::All"
    out += "<p><strong>Data processing / RECO</strong>"
    out += "<br/>This primary AOD dataset was processed from the RAW dataset by the following step (identical to 2011 RunA): "
    out += "<br/>Step: %s" % process
    out += "<br/>Release: %s" % release
    out += "<br/>Global tag: %s" % global_tag
    out += '\n        <br/><a href="/record/%s">%s</a>' % (
        CMS_2011_RUNA_CONFIG_RECORDS_LINK_INFO.get(afile, "FIXME"),
        generator_text,
    )
    out += "\n        </p>"
    # HLT trigger paths:
    out += "<p><strong>HLT trigger paths</strong>"
    out += "<br/>The possible HLT trigger paths in this dataset are:"
    trigger_paths = get_trigger_paths_for_dataset(dataset)
    for trigger_path in trigger_paths:
        out += '<br/><a href="/search?q=%s">%s</a>' % (trigger_path, trigger_path)
    out += "</p>"
    return out


def get_trigger_paths_for_dataset(dataset):
    """Return list of trigger paths for given dataset."""
    return FWYZARD.get(dataset, [])


def get_dataset_index_files(dataset_full_name):
    """Return list of dataset file information {path,size} for the given dataset."""
    files = []
    dataset_index_file_base = get_dataset_index_file_base(dataset_full_name)
    output = subprocess.getoutput(
        "ls ./inputs/eos-file-indexes/ | grep " + dataset_index_file_base
    )
    for line in output.split("\n"):
        afile = line.strip()
        if afile.endswith(".txt") or afile.endswith(".json"):
            # take only TXT files
            afile_uri = (
                XROOTD_URI_BASE
                + get_dataset_location(dataset_full_name)
                + "/file-indexes/"
                + afile
            )
            afile_size = get_file_size("./inputs/eos-file-indexes/" + afile)
            afile_checksum = get_file_checksum("./inputs/eos-file-indexes/" + afile)
            files.append((afile_uri, afile_size, afile_checksum))
    return files


def get_doi(dataset_full_name):
    "Return DOI for the given dataset."
    return DOI_INFO[dataset_full_name]


def create_record(recid, dataset):
    """Create record for the given dataset."""

    rec = {}

    recid_validated_runs = "1001"
    global_tag = "FT_53_LV5_AN1"
    release = "CMSSW_5_3_32"
    version = "12Oct2013-v1"
    run_period = "Run2011B"
    dataset_full_name = "/" + dataset + "/" + run_period + "-" + version + "/" + "AOD"
    year_created = run_period[3:7]
    year_published = "2020"

    rec["abstract"] = {}
    rec["abstract"]["description"] = (
        "<p>"
        + dataset
        + " primary dataset in AOD format from RunB of 2011. Run period from run number {0} to {1}.".format(
            dataset == "ZeroBias" and 177989 or 175833,
            dataset == "ZeroBias" and 178004 or 180252,
        )
        + "</p><p>"
        + "This dataset contains all runs from 2011 RunB. The list of validated runs, which must be applied to all analyses, can be found in"
        "</p>"
    )
    rec["abstract"]["links"] = [
        {"recid": recid_validated_runs},
    ]

    rec["accelerator"] = "CERN-LHC"

    rec["collaboration"] = {}
    rec["collaboration"]["name"] = "CMS collaboration"
    rec["collaboration"]["recid"] = "451"

    rec["collections"] = [
        "CMS-Primary-Datasets",
    ]

    rec["collision_information"] = {}
    rec["collision_information"]["energy"] = "7TeV"
    rec["collision_information"]["type"] = "pp"

    rec["date_created"] = [
        year_created,
    ]
    rec["date_published"] = year_published
    rec["date_reprocessed"] = year_created

    rec["distribution"] = {}
    rec["distribution"]["formats"] = ["aod", "root"]
    rec["distribution"]["number_events"] = get_number_events(dataset_full_name)
    rec["distribution"]["number_files"] = get_number_files(dataset_full_name)
    rec["distribution"]["size"] = get_size(dataset_full_name)

    rec["doi"] = get_doi(dataset_full_name)

    rec["experiment"] = "CMS"

    rec["files"] = []
    rec_files = get_dataset_index_files(dataset_full_name)
    for index_type in [".json", ".txt"]:
        index_files = [f for f in rec_files if f[0].endswith(index_type)]
        for file_number, (file_uri, file_size, file_checksum) in enumerate(index_files):
            rec["files"].append(
                {
                    "checksum": "sha1:" + file_checksum,
                    "description": dataset
                    + " AOD dataset file index ("
                    + str(file_number + 1)
                    + " of "
                    + str(len(index_files))
                    + ") for access to data via CMS virtual machine",
                    "size": file_size,
                    "type": "index" + index_type,
                    "uri": file_uri,
                }
            )

    rec["license"] = {}
    rec["license"]["attribution"] = "CC0"

    rec["methodology"] = {}
    rec["methodology"]["description"] = create_selection_information(
        dataset, dataset_full_name
    )

    rec["publisher"] = "CERN Open Data Portal"

    rec["recid"] = str(recid)

    rec["run_period"] = [
        run_period,
    ]

    rec["system_details"] = {}
    rec["system_details"]["global_tag"] = global_tag
    rec["system_details"]["release"] = release

    rec["title"] = dataset_full_name

    rec["title_additional"] = (
        dataset
        + " primary dataset in AOD format from "
        + run_period[0:3]
        + run_period[-1]
        + " of "
        + year_created
        + " ("
        + dataset_full_name
        + ")"
    )

    rec["type"] = {}
    rec["type"]["primary"] = "Dataset"
    rec["type"]["secondary"] = [
        "Collision",
    ]

    rec["usage"] = {}
    rec["usage"][
        "description"
    ] = "You can access these data through the CMS Virtual Machine. See the instructions for setting up the Virtual Machine and getting started in"
    rec["usage"]["links"] = [
        {
            "description": "How to install the CMS Virtual Machine",
            "url": "/vm/cms/2011",
        },
        {
            "description": "Getting started with CMS open data",
            "url": "/getting-started/cms/2011",
        },
    ]

    rec["validation"] = {}
    rec["validation"][
        "description"
    ] = "During data taking all the runs recorded by CMS are certified as good for physics analysis if all subdetectors, trigger, lumi and physics objects (tracking, electron, muon, photon, jet and MET) show the expected performance. Certification is based first on the offline shifters evaluation and later on the feedback provided by detector and Physics Object Group experts. Based on the above information, which is stored in a specific database called Run Registry, the Data Quality Monitoring group verifies the consistency of the certification and prepares a json file of certified runs to be used for physics analysis. For each reprocessing of the raw data, the above mentioned steps are repeated. For more information see:"
    rec["validation"]["links"] = [
        {
            "description": "CMS data quality monitoring: Systems and experiences",
            "url": "http://iopscience.iop.org/1742-6596/219/7/072020/pdf/1742-6596_219_7_072020.pdf",
        },
        {
            "description": "The CMS Data Quality Monitoring software experience and future improvements",
            "url": "http://cds.cern.ch/record/1631039/files/CR2013_418.pdf",
        },
        {
            "description": "The CMS data quality monitoring software: experience and future prospects",
            "url": "http://iopscience.iop.org/1742-6596/513/3/032024/pdf/1742-6596_513_3_032024.pdf",
        },
    ]

    return rec


def create_records(recid_start, datasets):
    """Create records."""
    records = []
    recid = recid_start
    for dataset in datasets:
        records.append(create_record(recid, dataset))
        recid += 1
    return records


def print_records(records):
    """Print records."""
    print("[")
    for (idx, rec) in enumerate(records):
        print(json.dumps(rec, indent=2, sort_keys=True))
        if idx == len(records) - 1:
            pass
        else:
            print(",")
    print("]")


@click.command()
def main():
    "Do the job."
    populate_fwyzard()
    populate_fileinfo()
    populate_doiinfo()
    datasets = [
        "BTag",
        "DoubleElectron",
        "DoubleMu",
        "ElectronHad",
        "HT",
        "Jet",
        "MET",
        "MinimumBias",
        "MuEG",
        "MuHad",
        "MuOnia",
        "MultiJet",
        "Photon",
        "PhotonHad",
        "SingleElectron",
        "SingleMu",
        "Tau",
        "TauPlusX",
    ]
    records = create_records(270, datasets)
    print_records(records)


if __name__ == "__main__":
    main()
