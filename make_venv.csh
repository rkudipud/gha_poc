#!/usr/intel/bin/tcsh -f

# Change directory of pip cache data
#  else it will default to the home directory
#   and could run out of disk space
set pip_cache = "/tmp/pip_pycth_${USER}"
if (! -d $pip_cache) then
  mkdir $pip_cache
endif

echo "Installing python venv and package dependencies"
/usr/intel/bin/python3.11.1 -m venv venv 
source venv/bin/activate.csh

# setup the proxy server
setenv http_proxy http://proxy-chain.intel.com:911 
setenv https_proxy http://proxy-chain.intel.com:912 

# run pip install
# Old way: created with: pip freeze | awk -F '=' '{print $1}' | grep -v nbfeeder | grep -v nbdask | sort > requirements.txt
# New: created with: pigar generate
# pigar will get a bare minimum and not all 185 libraries
pip --cache-dir $pip_cache install -r requirements.txt

# run pip install for netbatch packages
# done after regular pip install to get the dask-jobqueue package.
# These come from different index-url, so they cannot be added to the requirements.txt
# You can specify the exact file in the requirements.txt by using an @ with the url to the .whl file
# But this does get latest version.
# If more than 2 need to come from a special URL, put them in their own requirements with -i <index-url> at the top
pip --cache-dir $pip_cache install nbfeeder==1.51 --index-url https://ubit-artifactory-il.intel.com/artifactory/api/pypi/swiss-python-il-local/simple
pip --cache-dir $pip_cache install nbdask==1.51 --index-url https://ubit-artifactory-il.intel.com/artifactory/api/pypi/swiss-python-il-local/simple

rm -rf $pip_cache
