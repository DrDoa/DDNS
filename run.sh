#!/usr/bin/env bash
# start

RUN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )";


today=$(date +%m_%d_%Y)

function checkAndMakedir()
{
  local cmkdir_path=$1
  if [ ! -d "$1" ]; then
    mkdir "$1"
  fi
}


checkAndMakedir "${RUN_DIR}/logs/${today}"


currentDir=''


function walk()
{
  for file in `ls $1`
  do
    local path=$1"/"$file
    if [ -d "$path" ]
     then
        currentDir="$file"
      # echo "DIR     $path"
      # echo "DIRNAME $file"
      walk $path
    else
         # echo "  [CURDIR]   [${currentDir}]"
         # echo "    [FILE]   [$path]"
         echo "[PROCESSING]   [$file]"
         local logDirPath="${RUN_DIR}/logs/${today}/${currentDir}"
         checkAndMakedir "${logDirPath}"
         python "$RUN_DIR/run.py" -c ${path} >> "${logDirPath}/${file}.log" & 
    fi
  done
}

 
walk $RUN_DIR/configs  

 
# end
#if [ $# -ne 1 ]
#then
#  echo "USAGE: $0 TOP_DIR"
#else
#  walk $1
#fi
