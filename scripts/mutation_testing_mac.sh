#!/usr/bin/env bash

game_name="$1"  # The first command-line argument represents the path to the folder

wieght_file="$2"  # The second command-line argument represents the path to the weight file name

# Check if the path is provided
if [ -z "$game_name" ]; then
    echo "Usage: ./script.sh <game_name>"
    exit 1
fi

cd ..

# Retrieve the names of all folders in the path
#folder_names=()
#for folder in game/"$game_name"/mutants/*/; do
#    folder_names+=("${folder%/}")
#done
folder_names=$(find games/"$game_name"/mutants/* -type d -maxdepth 1 -exec basename {} \;)

for ((counter=5; counter<=30; counter++)); do
  echo "Run # '$counter'"
  # Use the folder names in a command
  for folder_name in $folder_names; do
      if [[ $folder_name != "baseline" && $folder_name != "__pycache__" && $folder_name != "__pycache__" ]]; then
          #echo "Folder name is not 'pycache'"
          echo "Processing mutant: $folder_name"
          #echo "What"
          python run.py --agent=merlin --mode=eval --exp_name=clean --weights_dir="$game_name"-wieghts/"$wieght_file" --game=$game_name --mutant=$folder_name
  #    else
  #        echo "Folder name is 'pycache'"
      fi

      # Replace the echo statement with your desired command that uses the folder names
      # Example: command "$folder_name"
  done

  # Name of the folder to be created
  run_folder_name=mutation-testing-logs/dqn/"$game_name"/run_"$counter"

  # Create the folder if it doesn't exist
  if [ ! -d "$run_folder_name" ]; then
      mkdir "$run_folder_name"
      echo "Folder '$run_folder_name' created."
  else
      echo "Folder '$run_folder_name' already exists."
  fi

  # Move all .tsv files to the created folder
  mv mutation-testing-logs/dqn/"$game_name"/*.tsv "$run_folder_name"/
  # Move all .tsv files to the created folder
  mv mutation-testing-logs/dqn/"$game_name"/*.csv "$run_folder_name"/

  echo "All .tsv files moved to '$run_folder_name' folder."

done
read userInput