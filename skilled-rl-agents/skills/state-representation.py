import wandb
import torch
from atariari.methods.utils import get_argparser
from atariari.benchmark.episodes import get_episodes
from atariari.methods.encoders import NatureCNN
from atariari.methods.stdim import InfoNCESpatioTemporalTrainer

def train_encoder(args):
    device = torch.device("cuda:" + str(args.cuda_id) if torch.cuda.is_available() else "cpu")
    tr_eps, val_eps = get_episodes(steps=args.pretraining_steps,
                                 env_name=args.env_name,
                                 seed=args.seed,
                                 num_processes=args.num_processes,
                                 num_frame_stack=args.num_frame_stack,
                                 downsample=not args.no_downsample,
                                 color=args.color,
                                 entropy_threshold=args.entropy_threshold,
                                 collect_mode=args.probe_collect_mode,
                                 train_mode="train_encoder",
                                 checkpoint_index=args.checkpoint_index,
                                 min_episode_length=args.batch_size)

    observation_shape = tr_eps[0][0].shape
    if args.encoder_type == "Nature":
        encoder = NatureCNN(observation_shape[0], args)
    else:
        assert False, "method {} has no trainer".format(args.method)

    encoder.to(device)
    torch.set_num_threads(1)

    config = {}
    config.update(vars(args))
    config['obs_space'] = observation_shape
    trainer = InfoNCESpatioTemporalTrainer(encoder, config, device=device)
    trainer.train(tr_eps, val_eps)

    return encoder

parser = get_argparser()
args = parser.parse_args()
tags = ['pretraining-only', 'state_rep']
wandb.init(project=args.wandb_proj, entity="epai", tags=tags)
config = {}
config.update(vars(args))
wandb.config.update(config)
train_encoder(args)

# nohup python main.py --env-name PongNoFrameskip-v4 --num-frame-stack 4  --num-processes 1 --feature-size 512 --wandb-proj attskills --train-encoder > statepong#1.log 2>&1 &
