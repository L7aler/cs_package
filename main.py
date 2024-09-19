import numpy as np
import time; import datetime
import argparse

import data
from figures import Figures

if __name__ == '__main__':

    # Instantiate the parser
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'input_file', type=str, #required=True, 
        help='Name of input file (e.g. input.example_ExoMol)', 
        )

    parser.add_argument('--download', '-d', action='store_true')
    parser.add_argument('--cross_sections', '-cs', action='store_true')
    parser.add_argument('--save', '-s', action='store_true')
    parser.add_argument('--plot', action='store_true')

    parser.add_argument('--convert_to_pRT2', action='store_true')
    parser.add_argument('--convert_to_pRT3', action='store_true')

    # Index to read if multiple .trans files are given
    parser.add_argument('--trans_idx_min', '-i_min', default=0, type=int)
    parser.add_argument('--trans_idx_max', '-i_max', default=1, type=int)
    parser.add_argument('--show_pbar', action='store_true')
    
    # Optionally, overwrite the P and T values of conf
    parser.add_argument('--P', type=float, default=None)
    parser.add_argument('--T', type=float, default=None)

    parser.add_argument('--tmp_output_file', '-out', type=str, default='cross{}.hdf5')
    args = parser.parse_args()

    # Import input file as 'conf'
    input_string = str(args.input_file).replace('.py', '').replace('/', '.')
    conf = __import__(input_string, fromlist=[''])

    # Download from the ExoMol/HITEMP database
    if args.download:
        if conf.database.lower() == 'exomol':
            data.ExoMol.download_data(conf)
        elif conf.database.lower() in ['hitemp', 'hitran']:
            data.HITEMP.download_data(conf)
        elif conf.database.lower() in ['vald', 'kurucz']:
            data.VALD_Kurucz.download_data(conf)

        import sys; sys.exit()
            
    # Load data
    D = data.load_data(conf)

    if args.cross_sections:

        tmp_output_file = args.tmp_output_file

        # Update P/T-grid and temporary output file to avoid overwriting
        if args.P is not None:
            conf.P_grid = np.array([args.P])
            tmp_output_file = tmp_output_file.replace('.hdf5', f'_P{args.P}.hdf5')
        if args.T is not None:
            conf.T_grid = np.array([args.T])
            tmp_output_file = tmp_output_file.replace('.hdf5', f'_T{args.T}.hdf5')

        i_min = args.trans_idx_min
        i_max = args.trans_idx_max

        time_start = time.time()

        # Compute the cross-sections and save in temporary files
        D.get_cross_sections(conf, tmp_output_file=tmp_output_file, i_min=i_min, i_max=i_max)
        
        time_finish = time.time()
        time_elapsed = time_finish - time_start
        print('\nTime elapsed (total): {}'.format(str(datetime.timedelta(seconds=time_elapsed))))

    if args.save:
        # (Possibly) combine cross-sections from different .trans files
        D.combine_cross_sections(conf)
        
    if args.plot:
        F = Figures(
            D, wave_range=[(1/3,50.0), (1.05,1.35), (1.9,2.5), (2.29,2.4), (2.332,2.339)]
            )
        F.plot_P(
            T=1000, P=10**np.array([-4,-2,0,2], dtype=np.float64), 
            ylim=(1e-28,1e-16), save_file=f'{conf.output_dir}/plots/P.pdf'
            )
        F.plot_T(
            P=1, T=np.array([500,1000,1500,2000,2500]), 
            ylim=(1e-28,1e-16), save_file=f'{conf.output_dir}/plots/T.pdf'
            )

    if args.convert_to_pRT2:
        D.convert_to_pRT2_format(
            out_dir=conf.pRT['out_dir'], 
            pRT_wave_file=conf.pRT['wave'], 
            make_short_file=conf.pRT['make_short_file']
        )
        
    if args.convert_to_pRT3:
        
        isotopologue_id = getattr(conf, 'isotopologue_id', None) # dict(Mg=12)
        assert isotopologue_id is not None, 'isotopologue_id must be defined in input file'
        
        kwargs = {
                    'resolving_power': 1e6, # R = lambda / dlambda, default: 1e6
                    'contributor': 'Dario Gonzalez Picos',
                    'doi': 'None', # change if you have a publication with this data
        }
                      
        D.convert_to_pRT3_format(
            out_dir=conf.pRT['out_dir'], 
            pRT_wave_file=conf.pRT['wave'], 
            isotopologue_id=isotopologue_id,
            **kwargs
        )