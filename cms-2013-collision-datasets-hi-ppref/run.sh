#!/bin/sh

## 1) create EOS file indexes:
#
# simko@lxplus8> export EOS_MGM_URL=root://eospublic.cern.ch
# simko@lxplus8> mkdir -p inputs/eos-file-indexes
# simko@lxplus8> python2 ./code/create_eos_file_indexes.py
# simko@laptop> rsync -av simko@lxplus8.cern.ch:/<remote-path>/inputs/eos-file-indexes/ ./inputs/eos-file-indexes

## 2) populate inputs/das-json-store/*.json by running code/create-das-json-store.sh as CERNAPCMS on lxplus8
#
# cernapcms@lxplus8> ./code/create-das-json-store.sh
# simko@laptop> rsync -av cernapcms@lxplus8.cern.ch:tibor/data-curation/cms-2013-collision-datasets-hi-ppref/inputs/das-json-store/ ./inputs/das-json-store

## 3) populate inputs/das-json-config-store/*.json by running code/create-das-json-config-store.sh as CERNAPCMS on lxplus8
#
# cernapcms@lxplus8> ./code/create-das-json-config-store.sh
# simko@laptop> rsync -av cernapcms@lxplus8.cern.ch:tibor/data-curation/cms-2013-collision-datasets-hi-ppref/inputs/das-json-config-store/ ./inputs/das-json-config-store
# simko@laptop> rsync -av cernapcms@lxplus8.cern.ch:tibor/data-curation/cms-2013-collision-datasets-hi-ppref/inputs/config-store/ ./inputs/config-store

## 5) create collision data

python ./code/create_dataset_records.py > ./outputs/cms-primary-datasets-HIpp-Run2013A.json

## 6) check the validity of resulting JSON files

jsonlint -q ./outputs/*.json

## 7) copy them to CERN Open Data fixtures directory

\cp outputs/*.json ../../opendata.cern.ch/cernopendata/modules/fixtures/data/records
