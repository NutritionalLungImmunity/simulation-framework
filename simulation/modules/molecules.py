import json

import attr
import numpy as np

from simulation.coordinates import Voxel
from simulation.grid import RectangularGrid
from simulation.module import Module, ModuleState
from simulation.modules.geometry import GeometryState, TissueTypes
from simulation.molecule import MoleculeGrid, MoleculeTypes
from simulation.state import State


def molecule_grid_factory(self: 'MoleculesState'):
    return MoleculeGrid(grid=self.global_state.grid)


@attr.s(kw_only=True, repr=False)
class MoleculesState(ModuleState):
    grid: MoleculeGrid = attr.ib(default=attr.Factory(molecule_grid_factory, takes_self=True))


class Molecules(Module):
    name = 'molecules'
    StateClass = MoleculesState

    def initialize(self, state: State):
        molecules: MoleculesState = state.molecules
        geometry: GeometryState = state.geometry

        # check if the geometry array is empty
        if not np.any(geometry.lung_tissue):
            raise RuntimeError('geometry molecule has to be initialized first')

        molecules_config = self.config.get('molecules')
        json_config = json.loads(molecules_config)

        for molecule in json_config:
            name = molecule['name']
            init_val = molecule['init_val']
            init_loc = molecule['init_loc']

            if name not in [e.name for e in MoleculeTypes]:
                raise TypeError(f'Molecule {name} is not implemented yet')

            for loc in init_loc:
                if loc not in [e.name for e in TissueTypes]:
                    raise TypeError(f'Cannot find lung tissue type {loc}')

            molecules.grid.append_molecule_type(name)

            for loc in init_loc:
                molecules.grid.concentrations[name][
                    np.where(geometry.lung_tissue == TissueTypes[loc].value)
                ] = init_val

            if 'source' in molecule:
                source = molecule['source']
                incr = molecule['incr']
                if source not in [e.name for e in TissueTypes]:
                    raise TypeError(f'Cannot find lung tissue type {source}')

                molecules.grid.sources[name][
                    np.where(geometry.lung_tissue == TissueTypes[init_loc[0]].value)
                ] = incr

        return state

    def advance(self, state: State, previous_time: float):
        """Advance the state by a single time step."""
        molecules: MoleculesState = state.molecules

        # iron = molecules.grid['iron']
        # with open('testfile.txt', 'w') as outfile:
        #     for data_slice in iron:
        #         np.savetxt(outfile, data_slice, fmt='%-7.2f')

        for molecule in molecules.grid.types:
            self.degrade(molecules.grid[molecule])
            self.diffuse(molecules.grid[molecule], state.grid, state.geometry.lung_tissue)

        molecules.grid.incr()

        return state

    @classmethod
    def diffuse(cls, molecule: np.ndarray, grid: RectangularGrid, tissue):
        # TODO These 2 functions should be implemented for all moleculess
        # the rest of the behavior (uptake, secretion, etc.) should be
        # handled in the cell specific module.
        temp = np.zeros(molecule.shape)

        x_r = [-1, 0, 1]
        y_r = [-1, 0, 1]
        z_r = [-1, 0, 1]

        for index in np.argwhere(temp == 0):
            for x in x_r:
                for y in y_r:
                    for z in z_r:
                        zk = index[0] + z
                        yj = index[1] + y
                        xi = index[2] + x

                        if grid.is_valid_voxel(Voxel(x=xi,y=yj,z=zk)):
                            temp[index[2], index[1], index[0]] += molecule[zk, yj, xi] / 26
            
            if tissue[index[2], index[1], index[0]] == TissueTypes.AIR.value:
                temp[index[2], index[1], index[0]] = 0
        
        molecule[:] = temp[:]
        
        return

    @classmethod
    def degrade(cls, molecule: np.ndarray):
        # TODO These 2 functions should be implemented for all moleculess
        # the rest of the behavior (uptake, secretion, etc.) should be
        # handled in the cell specific module.
        return
