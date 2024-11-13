# Copyright 2024 DeepMind Technologies Limited
#
# AlphaFold 3 source code is licensed under CC BY-NC-SA 4.0. To view a copy of
# this license, visit https://creativecommons.org/licenses/by-nc-sa/4.0/
#
# To request access to the AlphaFold 3 model parameters, follow the process set
# out at https://github.com/google-deepmind/alphafold3. You may only use these
# if received directly from Google. Use is subject to terms of use available at
# https://github.com/google-deepmind/alphafold3/blob/main/WEIGHTS_TERMS_OF_USE.md

"""Downloads the AlphaFold v3.0 databases from GCS and decompresses them.

Curl is used to download the files and Zstandard (zstd) is used to decompress
them. Make sure both are installed on your system before running this script.
"""

import argparse
import concurrent.futures
import functools
import os
import subprocess
import sys


DATABASE_FILES = (
    'bfd-first_non_consensus_sequences.fasta.zst',
    'mgy_clusters_2022_05.fa.zst',
    'nt_rna_2023_02_23_clust_seq_id_90_cov_80_rep_seq.fasta.zst',
    'pdb_2022_09_28_mmcif_files.tar.zst',
    'pdb_seqres_2022_09_28.fasta.zst',
    'rfam_14_9_clust_seq_id_90_cov_80_rep_seq.fasta.zst',
    'rnacentral_active_seq_id_90_cov_80_linclust.fasta.zst',
    'uniprot_all_2021_04.fa.zst',
    'uniref90_2022_05.fa.zst',
)

BUCKET_PATH = 'https://storage.googleapis.com/alphafold-databases/v3.0'


def download_and_decompress(
    filename: str, *, bucket_path: str, download_destination: str
) -> None:
  """Downloads and decompresses a ztsd-compressed file."""
  print(
      f'STARTING download {filename} from {bucket_path} to'
      f' {download_destination}'
  )
  # Continue (`continue-at -`) for resumability of a partially downloaded file.
  # --progress-bar is used to show some progress in the terminal.
  # tr '\r' '\n' is used to remove the \r characters which are used by curl to
  # updated the progress bar, which can be confusing when multiple calls are
  # made at once.
  subprocess.run(
      args=(
          'curl',
          '--progress-bar',
          *('--continue-at', '-'),
          *('--output', f'{download_destination}/{filename}'),
          f'{bucket_path}/{filename}',
          *('--stderr', '/dev/stdout'),
      ),
      check=True,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      # Same as text=True in Python 3.7+, used for backwards compatibility.
      universal_newlines=True,
  )
  print(
      f'FINISHED downloading {filename} from {bucket_path} to'
      f' {download_destination}.'
  )

  print(f'STARTING decompressing of {filename}')

  # The original compressed file is kept so that if it is interupted it can be
  # resumed, skipping the need to download the file again.
  subprocess.run(
      ['zstd', '--decompress', '--force', f'{download_destination}/{filename}'],
      check=True,
  )
  print(f'FINISHED decompressing of {filename}')


def main(argv=('',)) -> None:
  """Main function."""
  parser = argparse.ArgumentParser(description='Downloads AlphaFold databases.')
  parser.add_argument(
      '--download_destination',
      default='/srv/alphafold3_data/public_databases',
      help='The directory to download the databases to.',
  )
  args = parser.parse_args(argv)

  if os.geteuid() != 0 and args.download_destination.startswith('/srv'):
    raise ValueError(
        'You must run this script as root to be able to write to /srv.'
    )

  destination = os.path.expanduser(args.download_destination)

  print(f'Downloading all data to: {destination}')
  os.makedirs(destination, exist_ok=True)

  # Download each of the files and decompress them in parallel.
  with concurrent.futures.ThreadPoolExecutor(
      max_workers=len(DATABASE_FILES)
  ) as pool:
    any(
        pool.map(
            functools.partial(
                download_and_decompress,
                bucket_path=BUCKET_PATH,
                download_destination=destination,
            ),
            DATABASE_FILES,
        )
    )

  # Delete all zstd files at the end (after successfully decompressing them).
  for filename in DATABASE_FILES:
    os.remove(f'{args.download_destination}/{filename}')

  print('All databases have been downloaded and decompressed.')


if __name__ == '__main__':
  main(sys.argv[1:])
