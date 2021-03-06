import os
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import pickle
import pdb
import uuid
#from phase_pick_generator import get_generator

def add_time(layers):
    input_layer,output_layer=layers

    output_slices=tf.split(output_layer,5,axis=-1)
    new_time=output_slices[-1]+input_layer[:,:,-1:]
    new_output_list=output_slices[0:4]+[new_time]
    
    output=tf.concat(output_slices[0:4]+[new_time],axis=2)
    return output

def lon_loss(y_true,y_pred):
   mask=tf.cast(tf.not_equal(y_true[:,:,-1] ,tf.zeros_like(y_true[:,:,-1])),'float32' )
   lonfac=1/0.0009280954987236569/1000
   return tf.reduce_mean(tf.square(y_true[:,:,0]-y_pred[:,:,0])*mask)*lonfac

def lat_loss(y_true,y_pred):
    latfac=1/0.0008034709946970919/1000
    mask=tf.cast(tf.not_equal(y_true[:,:,-1] ,tf.zeros_like(y_true[:,:,-1])),'float32' )
    return tf.reduce_mean(tf.square(y_true[:,:,1]-y_pred[:,:,1])*mask)*latfac

def depth_loss(y_true,y_pred):
    depfac=1/0.01/1000
    mask=tf.cast(tf.not_equal(y_true[:,:,-1] ,tf.zeros_like(y_true[:,:,-1])),'float32' )
    return tf.reduce_mean(tf.square((y_true[:,:,2]-y_pred[:,:,2]))*mask)*depfac

def mag_loss(y_true,y_pred):
    magfac=1/0.02/1000
    mask=tf.cast(tf.not_equal(y_true[:,:,-1] ,tf.zeros_like(y_true[:,:,-1])),'float32' )
    return tf.reduce_mean(tf.square(y_true[:,:,3]-y_pred[:,:,3])*mask)*magfac

def time_loss(y_true,y_pred):
    timefac=1/2.8935185185185184e-06/1000
    mask=tf.cast(tf.not_equal(y_true[:,:,-1] ,tf.zeros_like(y_true[:,:,-1])),'float32' )
    return tf.reduce_mean(tf.square(y_true[:,:,4]-y_pred[:,:,4])*mask)*timefac
    
def loss(y_true,y_pred):
    
    return (lon_loss(y_true,y_pred)
            +lat_loss(y_true,y_pred)
            +depth_loss(y_true,y_pred)
            +mag_loss(y_true,y_pred)
            +time_loss(y_true,y_pred))

def build_model(batch_size=32,use_residual=False):

    input_layer=tf.keras.layers.Input(batch_shape=(batch_size,None,5))
    lstm_f=tf.keras.layers.LSTM(100,return_sequences=True,stateful=True,recurrent_dropout=0.05)(input_layer)
    lstm_f=tf.keras.layers.LSTM(100,return_sequences=True,stateful=True)(lstm_f)
    out_head=tf.keras.layers.Dense(50)(lstm_f)
    out_head=tf.keras.layers.LeakyReLU()(out_head)
    out_head=tf.keras.layers.Dense(50)(out_head)
    out_head=tf.keras.layers.LeakyReLU()(out_head)
    out_head=tf.keras.layers.Dense(50)(out_head)
    out_head=tf.keras.layers.LeakyReLU()(out_head)

    regression=tf.keras.layers.Dense(5)(out_head)
    if use_residual:
        regression=tf.keras.layers.Lambda(add_time)([input_layer,regression])

    classification=tf.keras.layers.Dense(1,activation='sigmoid')(out_head)

    model =tf.keras.models.Model(input_layer,[regression,classification])
    opt=tf.keras.optimizers.Adam(1e-3)
    model.compile(loss=[loss,'binary_crossentropy'],optimizer=opt, metrics=[[lon_loss,lat_loss,depth_loss,mag_loss,time_loss],[]])
    return model

if __name__=='__main__':
   m= build_model(use_residual=True)
   m.summary()
   m= build_model(use_residual=False)
   m.summary()
