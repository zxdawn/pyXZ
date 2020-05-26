'''
INPUT:
    WRF-Chem mechanism file:
        *.eqn

    Required species

OUTPUT:
    Varnames in IRR*.nc file

UPDATE:
    Xin Zhang:
       05/25/2020: Basic
'''

import re
import pandas as pd


def read_eqn(dir, eqn_file, species):
    '''
    Read the equations from the mechanism file
    '''

    # create the empty DataFrame
    col_names = ['reactants', 'products']
    equations = pd.DataFrame(columns=col_names)

    with open(dir+eqn_file, 'r') as f:
        for line in f:
            # the species is in the right side of equation
            if species in line.split('=')[-1]:
                reaction = re.split('} | :', line)[1]
                # delete space and tab
                reaction = re.sub(r'\s+', '', reaction)
                # get the content after "="
                right = reaction.split('=')[1]
                # get the index of species
                species_idx = right.index(species)
                # check whether there's number before the species
                if species_idx != 0 and right[species_idx-1] != '+':
                    # if the character two digits before the species is letter
                    # then it is actually another species
                    # which just contains the substring of species
                    if species_idx-1 != 0 and right[species_idx-2].isalpha():
                            continue

                # only the reactants are right ...
                # I don't decide to fix it now,
                # as I only need the reactants to generate the IRR varname
                equations = equations.append({'reactants': reaction.split('=')[0],
                                              'products': reaction.split('=')[1]
                                              },
                                             ignore_index=True
                                             )

    return equations


def convert_names(row):
    '''
    Convert reactants to varnames in IRR files
    '''

    return row['reactants'].upper().replace('+', '_').replace('{_M}', '') + '_IRR'


def irr_varnames(equations):
    '''
    Principle of varname of IRR:
       Omit {+M}, use "_" instead of "+" and "_IRR" as suffix
    '''

    equations['irr_varname'] = equations.apply(lambda row: convert_names(row), axis=1)
    return equations


def main():
    # set dir and equation file
    dir = './data/wrfchem/mechanisms/'
    eqn_file = 'mozcart.eqn'
    species = 'NO2'

    # read equations
    equations = read_eqn(dir, eqn_file, species)
    # get varnames in IRR files
    irr_varnames(equations)['irr_varname']


if __name__ == '__main__':
    main()
