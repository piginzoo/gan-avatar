
from keras.datasets import mnist
from keras.layers import Input,Dense,Reshape,Flatten,Dropout
from keras.layers import BatchNormalization,Activation,ZeroPadding2D
from keras.layers import LeakyReLU
from keras.layers import UpSampling2D,Conv2D
from keras.models import Sequential,Model
from keras.optimizers import Adam,RMSprop
import time
from keras.models import load_model
from keras.preprocessing import image
import os
import matplotlib.pyplot as plt
import numpy as np

class DCGAN():
    def __init__(self):
        self.img_rows = 96;
        self.img_cols = 96;
        self.channels = 3;
        self.img_shape=(self.img_rows,self.img_cols,self.channels)
        self.latent_dim =100

        optimizer = Adam(0.0002,0.5)
        # optimizerD =RMSprop(lr=0.0008, clipvalue=1.0, decay=6e-8)
        # optimizerG = RMSprop(lr=0.0004, clipvalue=1.0, decay=6e-8)

        #对判别器进行构建和编译
        self.discriminator = self.build_discriminator()
        self.discriminator.compile(loss='binary_crossentropy',optimizer=optimizer,metrics=['accuracy'])
        print("构建了D")

        #对生成器进行构造
        self.generator = self.build_generator()
        print("构建了G")
        # The generator takes noise as input and generates imgs
        z = Input(shape=(self.latent_dim,))
        gen_img = self.generator(z)
        # 总体模型只对生成器进行训练
        # 靠！可以这么写么？之前的模型self.discriminator不会收影响么？难道因为已经compile了么？表示怀疑？？？
        # https://stackoverflow.com/questions/45154180/how-to-dynamically-freeze-weights-after-compiling-model-in-keras
        # https://github.com/keras-team/keras/blob/master/examples/mnist_acgan.py
        self.discriminator.trainable = False 

        # 从生成器中生成的图 经过判别器获得一个valid
        valid = self.discriminator(gen_img)

        # model = Model(inputs=[a1, a2], outputs=[b1, b3, b3])
        self.combined = Model(z,valid)
        self.combined.compile(loss='binary_crossentropy', optimizer=optimizer)

        print("################生成器+判别器结构################")
        self.combined.summary()

        print("################判别器结构################")
        self.discriminator.summary()

    # G
    def build_generator(self):
        model = Sequential()

        model.add(Dense(512*6*6,activation='relu',input_dim=self.latent_dim))  #输入维度为100，输出128*7*7
        model.add(Reshape((6,6,512)))

        model.add(UpSampling2D())  #进行上采样，变成14*14*128
        model.add(Conv2D(256,kernel_size=5,padding='same'))
        model.add(BatchNormalization(momentum=0.8))#该层在每个batch上将前一层的激活值重新规范化，即使得其输出数据的均值接近0，其标准差接近1优点（1）加速收敛 （2）控制过拟合，可以少用或不用Dropout和正则 （3）降低网络对初始化权重不敏感 （4）允许使用较大的学习率
        model.add(Activation("relu"))#

        model.add(UpSampling2D())
        model.add(Conv2D(128, kernel_size=5, padding="same"))
        model.add(BatchNormalization(momentum=0.8))
        model.add(Activation("relu"))

        model.add(UpSampling2D())
        model.add(Conv2D(64, kernel_size=5, padding="same"))
        model.add(BatchNormalization(momentum=0.8))
        model.add(Activation("relu"))

        model.add(UpSampling2D())
        model.add(Conv2D(self.channels, kernel_size=5, padding="same"))
        model.add(Activation("tanh"))

        print("生成G结构")
        model.summary()  #打印网络参数

        noise = Input(shape=(self.latent_dim,))
        img = model(noise)
        return  Model(noise,img)  #定义一个 一个输入noise一个输出img的模型

    def build_discriminator(self):
        dropout = 0.25
        model = Sequential()

        model.add(Conv2D(64, kernel_size=5, strides=2, input_shape=self.img_shape, padding="same"))
        model.add(LeakyReLU(alpha=0.2))
        model.add(Dropout(dropout))

        model.add(Conv2D(128, kernel_size=5, strides=2, padding="same"))
        model.add(ZeroPadding2D(padding=((0, 1), (0, 1))))
        model.add(BatchNormalization(momentum=0.8))
        model.add(LeakyReLU(alpha=0.2))
        model.add(Dropout(dropout))

        model.add(Conv2D(256, kernel_size=5, strides=2, padding="same"))
        model.add(BatchNormalization(momentum=0.8))
        model.add(LeakyReLU(alpha=0.2))
        model.add(Dropout(dropout))

        model.add(Conv2D(512, kernel_size=5, strides=1, padding="same"))
        model.add(BatchNormalization(momentum=0.8))
        model.add(LeakyReLU(alpha=0.2))
        model.add(Dropout(dropout))

        model.add(Flatten())
        model.add(Dense(1, activation='sigmoid'))

        print("判别器D结构")
        model.summary()

        img = Input(shape=self.img_shape)
        validity = model(img)

        return Model(img,validity)

    def set_trainability(self,model, trainable=False):
        model.trainable = trainable
        for layer in model.layers:
            layer.trainable = trainable        

    def train(self,epochs,batch_size=64,save_interval = 800,d_loop=5,g_loop=1,debug=False):
        if (debug):
            print("调试模式，调整参数")
            batch_size = 3
            save_interval=1
            d_loop=1
        # Adversarial ground truths
        valid = np.ones((batch_size, 1))
        fake = np.zeros((batch_size, 1))
        dir_name = 'data/faces'
        img_names = os.listdir(os.path.join(dir_name))
        img_names = np.array(img_names)

        for epoch in range(epochs):

            start = time.time()
            # ---------------------
            #  Train Discriminator
            # ---------------------
            d_loss_sum = 0
            # 按照论文里说的，判别器多训练几次，比如5次。
            for i in range(d_loop):
                imgs = self.load_batch_imgs(batch_size,img_names,dir_name)
                d_loss_real = self.discriminator.train_on_batch(imgs, valid)

                noise = np.random.normal(0, 1, (batch_size, self.latent_dim))
                gen_imgs = self.generator.predict(noise)
                d_loss_fake = self.discriminator.train_on_batch(gen_imgs, fake)

                d_loss_sum += 0.5 * np.add(d_loss_real, d_loss_fake)

            d_loss = d_loss_sum / d_loop

            # ---------------------
            #  Train Generator
            # ---------------------

            # Train the generator (wants discriminator to mistake images as real)
            g_loss = self.combined.train_on_batch(noise, valid)

            # Plot the progress
            print ("%d | D loss: %f | Acc.: %.2f%% | G loss: %f | Time: %f" % (epoch, d_loss[0], 100*d_loss[1], g_loss, time.time()-start))

            # If at save interval => save generated image samples
            if epoch % save_interval == 0:
                self.combined.save('./model/combined_model_%d.h5'%epoch)
                self.discriminator.save('./model/discriminator_model_%d.h5'%epoch )
                self.save_imgs(epoch)


    def load_batch_imgs(self,batch_size,img_names,dirName):
        idx = np.random.randint(0, img_names.shape[0], batch_size)
        img_names = img_names[idx]
        img = []
        # 把图片读取出来放到列表中
        for i in range(len(img_names)):
            images = image.load_img(os.path.join(dirName, img_names[i]), target_size=(96, 96))
            x = image.img_to_array(images)
            x = np.expand_dims(x, axis=0)
            img.append(x)
            # print('loading no.%s image' % i)

        # 把图片数组联合在一起

        x = np.concatenate([x for x in img])
        x = x / 127.5 - 1.
        return x


    def save_imgs(self, epoch):
        r, c = 5, 5
        noise = np.random.normal(0, 1, (r * c, self.latent_dim))  #高斯分布，均值0，标准差1，size= (5*5, 100)
        gen_imgs = self.generator.predict(noise)
        gen_imgs = (gen_imgs + 1)*127.5

        fig, axs = plt.subplots(r, c)
        cnt = 0   #生成的25张图 显示出来
        for i in range(r):
            for j in range(c):
                axs[i,j].imshow(gen_imgs[cnt, :,:,:].astype(np.uint8))
                axs[i,j].axis('off')
                cnt += 1
        fig.savefig("data/gen/avatar_%d.png" % epoch)
        plt.close()

    def loadModel(self):
        self.combined = load_model('./model/combined_model_last.h5')
        self.discriminator = load_model('./model/discriminator_model_last.h5')

if __name__ == '__main__':
    import sys
    DEBUG = False
    if (sys.argv==2):
        print("调试模式")
        DEBUG = True
    dcgan = DCGAN()
    dcgan.train(epochs=40000, batch_size=64, save_interval=800,debug=DEBUG)