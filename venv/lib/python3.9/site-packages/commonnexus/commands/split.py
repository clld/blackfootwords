"""
Split a Mesquite multi-block NEXUS into individual NEXUS files per CHARACTERS/TREES block.

Output files will be named according to the pattern "<stem>_<BLOCK.TITLE>.{nex|trees}".
So a CHARACTERS block with TITLE 'x.y' will end up in 'mesquite_x.y.nex'.
"""
import pathlib

from commonnexus.cli_util import add_nexus
from commonnexus import Nexus


def register(parser):
    add_nexus(parser)
    parser.add_argument(
        '--stem',
        help='Stem of the filenames for the individual nexus files',
        default='mesquite')
    parser.add_argument(
        '--outdir',
        help="(Existing) directory to write the output to.",
        default='.')


def run(args):
    for block, suffix in dict(TREES='trees', CHARACTERS='nex').items():
        for i, block in enumerate(args.nexus.blocks[block], start=1):
            blocks = [block]
            if 'TAXA' in block.linked_blocks:
                blocks.insert(0, block.linked_blocks['TAXA'])
            nex = Nexus.from_blocks(*blocks)
            p = pathlib.Path(args.outdir) / '{}_{}.{}'.format(args.stem, block.title or i, suffix)
            nex.to_file(p)
            args.log.info('CHARACTERS block written to {}'.format(p))
