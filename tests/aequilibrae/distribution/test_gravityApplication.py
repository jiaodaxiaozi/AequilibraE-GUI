from unittest import TestCase
from aequilibrae.matrix import AequilibraEData, AequilibraeMatrix
from aequilibrae.distribution import SyntheticGravityModel, GravityApplication
import numpy as np

zones = 100

# row vector
args = {'entries': zones,
        'fields': ['rows'],
        'types': [np.float64]}

row_vector = AequilibraEData(**args)
row_vector.index[:] = np.arange(row_vector.entries) + 100
row_vector.rows[:] = row_vector.index[:] + np.random.rand(zones)[:]

# column vector
args['fields'] = ['columns']
column_vector = AequilibraEData(**args)
column_vector.index[:] = np.arange(column_vector.entries) + 100
column_vector.columns[:] = column_vector.index[:] + np.random.rand(zones)[:]


# balance vectors
column_vector.columns[:] = column_vector.columns[:] * (row_vector.rows.sum()/column_vector.columns.sum())

# Impedance matrix_procedures
args = {'zones': zones,
        'cores': 1,
        'names': ['impedance']}

matrix = AequilibraeMatrix(**args)
matrix.impedance[:, :] = np.random.rand(zones, zones)[:,:]
matrix.index[:] = np.arange(matrix.zones) + 100
matrix.computational_view(['impedance'])

model = SyntheticGravityModel()
model.function = 'EXPO'
model.beta = 0.1


class TestGravityApplication(TestCase):
    def test_apply(self):
        args = {'impedance': matrix,
                'rows': row_vector,
                'row_field': 'rows',
                'columns': column_vector,
                'column_field': 'columns',
                'model': model}

        distributed_matrix = GravityApplication(**args)
        distributed_matrix.apply()

        if distributed_matrix.gap > distributed_matrix.parameters['convergence level']:
            self.fail('Gravity application did not converge')