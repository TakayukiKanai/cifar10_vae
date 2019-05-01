import network
import cifar10_loader
import tensorflow as tf
import numpy as np
import pandas as pd
import argparse

parser = argparse.ArgumentParser(description='Training method')  # Create parser
parser.add_argument('model_type', help='set CNN or VAE')
parser.add_argument('log_dir')
parser.add_argument('epoch')
parser.add_argument('batch')
parser.add_argument('get_images_per_one_file',
                    help='Set the number of images for learning from data_batch_<n>.bin file. The max of it is 10000.')
parser.add_argument('gpu_id',
                    help='Specify GPU ID (If your computer does not mount GPU, CPU is only used for training.)')
args = parser.parse_args()

MODEL_TYPE = args.model_type
LOG_DIR = args.log_dir
EPOCH = int(args.epoch)
BATCH = int(args.batch)
Get_Images_Per_One_file = int(args.get_images_per_one_file)
GPU_ID = args.gpu_id

data_cfg = {
    'Path_to_save_cifar10_bin': './cifar-10-batches-bin/',
    'Load_file_num': 5,
    'Data_Augmentation_Ratio': 1,
    'Get_Images_Per_One_file': Get_Images_Per_One_file,
}

network_cfg = {
    'img_shape': [32, 32, 3],
    'latent_dim': 64,
    'log_path': './test_/',
    'log_overwrite_save': True,
}

# If you use GPU, please setting follow;
tf_config = tf.ConfigProto(
    gpu_options=tf.GPUOptions(
        # visible_device_list="0",  # specify GPU number
        visible_device_list=GPU_ID,  # specify GPU number
        allow_growth=True
    )
)


def train_vae(total_epoch=1000, batch_size=16, log_out_span=5, log_path=network_cfg['log_path']):
    # Data
    dataset = cifar10_loader.Cifar10(data_cfg)
    X_train, X_test, T_train, T_test, N_train, N_test \
        = dataset.fetch_bin_to_tensor(data_argumantation_int=data_cfg['Data_Augmentation_Ratio'], reshape3d=True)
    vae = network.VAE(network_cfg)

    # Iteration
    sess = tf.Session(config=tf_config)
    init_op = tf.global_variables_initializer()
    sess.run(init_op)
    train_loss_list = []
    learn_percent = 0.0
    saver = tf.train.Saver()
    log_writer = tf.summary.FileWriter(log_path, sess.graph)

    for epoch in range(total_epoch):
        print('epoch %d | ' % epoch, end='')
        sum_loss = 0
        perm = np.random.permutation(N_train)
        cnt = 0
        for i in range(0, N_train, batch_size):
            perm_batch = perm[i:i + batch_size]
            train_img = X_train[perm[i:i + batch_size]]
            batch_num = len(perm_batch)
            feed = {
                vae.img_plh: train_img,
                vae.real_batch_holder: batch_num,
            }
            _, loss, train_sum = sess.run([vae.optimize, vae.cost, vae.sum_train], feed_dict=feed)
            sum_loss += np.mean(loss) * batch_size
            cnt += 1
        loss_in_epoch = sum_loss / N_train
        train_loss_list.append(loss_in_epoch)
        print('Train loss %.3f | ' % (loss_in_epoch))

        if epoch % log_out_span == 0:
            # For Graphic
            generate_img_num = 100
            fig_name = vae.log_path + 'epoch_' + str(epoch) + '_.png'
            generated_normalized_img = vae.generate_from_gausian(generate_img_num)  # random sampling from repara-trick
            ndarray_img = sess.run(generated_normalized_img, feed_dict=feed)
            cifar10_loader.show_normalized_img_square(ndarray_img, save_fig_name=fig_name)
            # Test summary
            test_feed = {
                vae.img_plh: X_test,
                vae.real_batch_holder: len(X_test),
            }
            test_sum = sess.run(vae.sum_test, feed_dict=test_feed)
            saver.save(sess, log_path + 'graph1')  # save graph.meta,graph.index and so on ...
            log_writer.add_summary(train_sum, epoch)  # Write log to tensorboard of train state
            log_writer.add_summary(test_sum, epoch)  # same
            print('save')


def train_classification(total_epoch=1000, batch_size=16, log_out_span=5, log_path=network_cfg['log_path'],
                         out_to_csv=True):
    # Data
    dataset = cifar10_loader.Cifar10(data_cfg)
    X_train, X_test, T_train, T_test, N_train, N_test \
        = dataset.fetch_bin_to_tensor(data_argumantation_int=data_cfg['Data_Augmentation_Ratio'], reshape3d=True)
    # Model define
    cnn = network.CNN(network_cfg)
    # Config
    sess = tf.Session(config=tf_config)
    init_op = tf.global_variables_initializer()
    sess.run(init_op)
    saver = tf.train.Saver()
    log_writer = tf.summary.FileWriter(log_path, sess.graph)
    update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)  # For update NON-TRAINABLE parameter for batch norm.

    # For csv
    epoch_list = []
    train_loss_list = []
    train_acc_list = []
    test_loss_list = []
    test_acc_list = []

    def __eval_process(operation, data_type, all_data=False):
        X = None
        T = None
        N = batch_size
        loss_total = accu_total = 0
        summary_train = summary_test = None
        if data_type == 'train':
            is_training = True
            X = X_train
            T = T_train
            if all_data:
                N = N_train
        else:  # data_type == 'test'
            is_training = False
            X = X_test
            T = T_test
            if all_data:
                N = N_test
        for l in range(0, N, batch_size):
            img_batch = X[l:l + batch_size]
            t_batch = T[l:l + batch_size]
            real_batch = len(t_batch)
            feed = {
                cnn.img_plh: img_batch,
                cnn.t_plh: t_batch,
                cnn.real_batch_holder: real_batch,
                cnn.is_training_holder: is_training,  # For test mode
            }
            if operation == 'loss_and_accuracy_result':
                loss, accu = sess.run([cnn.loss, cnn.accuracy], feed_dict=feed)
                loss_total += np.mean(loss) * batch_size / N
                accu_total += np.mean(accu) * batch_size / N
            elif operation == 'summary_for_tensorboard':
                summary_train, summary_test = sess.run([cnn.sum_train, cnn.sum_test], feed_dict=feed)
            else:
                pass
        return loss_total, accu_total, summary_train, summary_test

    # Iteration
    for epoch in range(total_epoch):
        print('epoch %d | ' % epoch, end='')
        sum_acc = 0
        sum_loss = 0
        perm = np.random.permutation(N_train)
        cnt = 0
        for i in range(0, N_train, batch_size):
            perm_batch = perm[i:i + batch_size]
            train_img = X_train[perm[i:i + batch_size]]
            train_label = T_train[perm[i:i + batch_size]]
            batch_num = len(perm_batch)
            feed = {
                cnn.img_plh: train_img,
                cnn.t_plh: train_label,
                cnn.is_training_holder: True,
                cnn.real_batch_holder: batch_num,
            }
            _, __, loss, acc = sess.run([update_ops, cnn.optimize, cnn.loss, cnn.accuracy, ], feed_dict=feed)
            sum_acc += np.mean(acc) * batch_size
            sum_loss += np.mean(loss) * batch_size
            cnt += 1
        train_accuracy = sum_acc / N_train
        train_loss = sum_loss / N_train
        print('Train accuracy %.3f | ' % (train_accuracy), end='')
        print('Train loss %.3f | ' % (train_loss))

        if epoch % log_out_span == 0:
            # update tensorborad
            train_summary = __eval_process(operation='summary_for_tensorboard', data_type='train')[2]
            test_summary = __eval_process(operation='summary_for_tensorboard', data_type='test')[3]
            log_writer.add_summary(train_summary, epoch)  # Write log to tensorboard of train state
            log_writer.add_summary(test_summary, epoch)  # same
            if out_to_csv:
                # call whole data
                train_loss, train_accu, _, __ = __eval_process(operation='loss_and_accuracy_result', data_type='train')
                test_loss, test_accu, _, __ = __eval_process(operation='loss_and_accuracy_result', data_type='test')
                # For csv
                epoch_list.append(epoch)
                train_loss_list.append(train_loss)
                train_acc_list.append(train_accu)
                test_loss_list.append(test_loss)
                test_acc_list.append(test_accu)
                tmp_df = pd.DataFrame(
                    {'epoch': np.array(epoch_list),
                     'Train_loss': np.array(train_loss_list),
                     'Train_accuracy': np.array(train_acc_list),
                     'Test_loss': np.array(test_loss_list),
                     'Test_accuracy': np.array(test_acc_list),
                     })
                tmp_df.to_csv(log_path + 'loss_log.csv')
            else:
                pass
            # save model
            saver.save(sess, log_path + 'graph1')  # save graph.meta,graph.index and so on ...
            print('save')


if __name__ == '__main__':
    print('Training iter')
    if MODEL_TYPE == 'VAE':
        print('Variational AutoEncoder')
        train_vae(
            total_epoch=EPOCH,
            batch_size=BATCH,
            log_path=LOG_DIR
        )
    elif MODEL_TYPE == 'CNN':
        print('CLASSIFICATION')
        train_classification(
            total_epoch=EPOCH,
            batch_size=BATCH,
            log_path=LOG_DIR,
        )
    else:
        print('Specify appropriate MODEL name (CNN or VAE')
