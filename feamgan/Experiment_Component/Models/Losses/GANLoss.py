import torch
import torch.nn as nn
import torch.nn.functional as F


# Defines the GAN loss which uses either LSGAN or the regular GAN.
# When LSGAN is used, it is basically same as MSELoss,
# but it abstracts away the need to create the target label tensor
# that has the same size as the input
class GANLoss(nn.Module):
    def __init__(
        self,
        gan_mode,
        target_real_label=1.0,
        target_fake_label=0.0,
        tensor=torch.cuda.FloatTensor,
    ):
        super(GANLoss, self).__init__()
        self.real_label = target_real_label
        self.fake_label = target_fake_label
        self.real_label_tensor = None
        self.fake_label_tensor = None
        self.zero_tensor = None
        self.Tensor = tensor
        self.gan_mode = gan_mode
        if gan_mode == "ls":
            pass
        elif gan_mode == "original":
            pass
        elif gan_mode == "w":
            pass
        elif gan_mode == "hinge":
            pass
        else:
            raise ValueError("Unexpected gan_mode {}".format(gan_mode))

    def get_target_tensor(self, input, target_is_real):
        if target_is_real:
            if self.real_label_tensor is None:
                self.real_label_tensor = self.Tensor(1).fill_(self.real_label)
                self.real_label_tensor.requires_grad_(False)
            return self.real_label_tensor.expand_as(input)
        else:
            if self.fake_label_tensor is None:
                self.fake_label_tensor = self.Tensor(1).fill_(self.fake_label)
                self.fake_label_tensor.requires_grad_(False)
            return self.fake_label_tensor.expand_as(input)

    def loss(self, input, target_is_real, for_discriminator=True):
        if self.gan_mode == "original":  # cross entropy loss
            target_tensor = self.get_target_tensor(input, target_is_real)
            loss = F.binary_cross_entropy_with_logits(input, target_tensor)
            return loss
        elif self.gan_mode == "ls":
            target_tensor = self.get_target_tensor(input, target_is_real)
            return F.mse_loss(input, target_tensor)
        elif self.gan_mode == "hinge":
            if for_discriminator:
                if target_is_real:
                    minval = torch.min(input - 1, input * 0)
                    loss = -torch.mean(minval)
                else:
                    minval = torch.min(-input - 1, input * 0)
                    loss = -torch.mean(minval)
            else:
                assert target_is_real, (
                    "The generator's hinge loss must be aiming for real"
                )
                loss = -torch.mean(input)
            return loss
        else:
            # wgan
            if target_is_real:
                return -input.mean()
            else:
                return input.mean()

    def __call__(self, input, target_is_real, for_discriminator=True):
        # computing loss is a bit complicated because |input| may not be
        # a tensor, but list of tensors in case of multiscale discriminator
        if isinstance(input, list):
            loss = 0
            for pred_i in input:
                if isinstance(pred_i, list):
                    pred_i = pred_i[-1]
                loss_tensor = self.loss(pred_i, target_is_real, for_discriminator)
                bs = 1 if len(loss_tensor.size()) == 0 else loss_tensor.size(0)
                new_loss = torch.mean(loss_tensor.view(bs, -1), dim=1)
                loss += new_loss
            out = loss / len(input)  # TODO keep an eye on
            if out is None:
                print(
                    f"Error: Generator Loss calculation results in None. Traget is real: {target_is_real}. For discriminator: {for_discriminator}. Predicitons: {input}"
                )
            return out[0]
        else:
            return self.loss(input, target_is_real, for_discriminator)
