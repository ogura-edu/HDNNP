# -*- coding: utf-8 -*-

# define variables
from config import hp
from config import file_
from config import mpi

# import python modules
from time import time
from os import path
from os import makedirs
from datetime import datetime

# import own modules
from modules.data import DataGenerator
from modules.model import HDNNP
from modules.animator import Animator

datestr = datetime.now().strftime('%m%d-%H%M%S')
save_dir = path.join(file_.save_dir, datestr)
generator = DataGenerator('training', precond='pca')
if mpi.rank == 0:
    file = open(path.join(file_.progress_dir, 'progress-{}.out'.format(datestr)), 'w')
    stime = time()
    file.write("""
Rc:   {}
eta:  {}
Rs:   {}
lam:  {}
zeta: {}
learning_rate:       {}
learning_rate_decay: {}
mixing_beta:         {}
smooth_factor:       {}
batch_size:          {}
batch_size_growth:   {}
optimizer:           {}
""".format(','.join(map(str, hp.Rcs)), ','.join(map(str, hp.etas)), ','.join(map(str, hp.Rss)),
           ','.join(map(str, hp.lams)), ','.join(map(str, hp.zetas)),
           hp.learning_rate, hp.learning_rate_decay, hp.mixing_beta, hp.smooth_factor,
           hp.batch_size, hp.batch_size_growth, hp.optimizer))
    file.flush()
    makedirs(save_dir)

    for config, training_data, validation_data in generator:
        print '-----------------------{}-------------------------'.format(config)
        natom = training_data.natom
        ninput = training_data.ninput
        nsample = training_data.nsample
        composition = training_data.composition
        file.write("""

-------------------------{}-----------------------------

composition:   {}
natom:         {}
ninput:        {}
hidden_layers:
\t{}
nepoch:        {}
nsample:       {}

epoch   spent time        training_RMSE     training_dRMSE    training_tRMSE    validation_RMSE   validation_dRMSE  validation_tRMSE
""".format(config, dict(composition['number']), natom, ninput,
           '\n\t\t'.join(map(str, hp.hidden_layers)), hp.nepoch, nsample))
        file.flush()

        training_animator = Animator()
        validation_animator = Animator()
        hdnnp = HDNNP(natom, ninput, composition)
        hdnnp.load(save_dir)

        for m, training_RMSE, validation_RMSE in hdnnp.fit(training_data, validation_data, training_animator, validation_animator):
            t_RMSE, t_dRMSE, t_tRMSE = training_RMSE
            v_RMSE, v_dRMSE, v_tRMSE = validation_RMSE
            file.write('{:<7} {:<17.12f} {:<17.12f} {:<17.12f} {:<17.12f} {:<17.12f} {:<17.12f} {:<17.12f}\n'
                       .format(m+1, time()-stime, t_RMSE, t_dRMSE, t_tRMSE, v_RMSE, v_dRMSE, v_tRMSE))
            file.flush()

        training_animator.save_fig(datestr, config, 'training')
        validation_animator.save_fig(datestr, config, 'validation')
        hdnnp.save(save_dir)
        mpi.comm.Barrier()
    file.close()
    generator.save(save_dir)
else:
    for config, training_data, validation_data in generator:
        natom = training_data.natom
        ninput = training_data.ninput
        composition = training_data.composition
        hdnnp = HDNNP(natom, ninput, composition)
        if hdnnp.active:
            hdnnp.load(save_dir)
            for m, training_RMSE, validation_RMSE in hdnnp.fit(training_data, validation_data):
                pass
            hdnnp.save(save_dir)
        mpi.comm.Barrier()