-- 初始化管理员、开发人员、普通用户
-- 创建时间：2025-03-14 10:50:08

-- 添加管理员用户
INSERT INTO `user` (
    `username`, 
    `email`, 
    `password`, 
    `first_name`, 
    `last_name`, 
    `role`, 
    `avatar_path`, 
    `phone`, 
    `status`, 
    `created_at`, 
    `updated_at`
) VALUES (
    '望遇', 
    '1994043456@qq.com', 
    'scrypt:32768:8:1$mhu4GEku97eDNsUi$a39a1d98da9890866821eb2a36d1b4fb1e9d51bf370b274ef8b70e5604aef9c5e88c2d0cffb461b62609105335695bdaf0a7ce7ea143ecaf5ba0af9892f60bb3', -- 密码：admin-WZY
    '遇', 
    '望', 
    'ADMIN', 
    'static\\avatars\\1.jpg',
    '15527681581', 
    'INACTIVE', 
    NOW(), 
    NOW()
);

-- 添加开发人员用户
INSERT INTO `user` (
    `username`, 
    `email`, 
    `password`, 
    `first_name`, 
    `last_name`, 
    `role`, 
    `avatar_path`, 
    `phone`,
    `status`, 
    `created_at`, 
    `updated_at`
) VALUES (
    '汪忠毅', 
    '1583952973@qq.com', 
    'scrypt:32768:8:1$UtMwYLX1KSnmu6lk$3d7404f212eda78413ccab1c8a20a1836306d169cda9f5da635f92b3f3bd1c7649246d30feef87e093bb49508441eca5218c1bcec3638d33e0d68640732bc331', -- 密码：developer-WZY
    '忠毅', 
    '汪', 
    'DEVELOPER', 
    'static\\avatars\\2.jpg',
    '13871941390', 
    'INACTIVE', 
    NOW(), 
    NOW()
);

-- 添加普通用户
INSERT INTO `user` (
    `username`, 
    `email`, 
    `password`, 
    `first_name`, 
    `last_name`, 
    `role`, 
    `avatar_path`, 
    `phone`,
    `status`, 
    `created_at`, 
    `updated_at`
) VALUES (
    'WZY', 
    '122849730@qq.com', 
    'scrypt:32768:8:1$mWhiEV1orl2PKEmM$2a43af98b53f934dfec2841394dd5e5b40bd913b973f0c8b0aba7929a16e215f7aa03001378ea8c23a5d575f992a377eafa0789f19f6359d3d5a876ba973de84', -- 密码：user-WZY
    'ZY', 
    'W', 
    'USER', 
    'static\\avatars\\3.jpg',
    '19972406719',
    'INACTIVE', 
    NOW(), 
    NOW()
);

-- 注意：
-- 1. 密码字段使用了 werkzeug.security.generate_password_hash 生成的哈希值
-- 2. 实际使用时，建议修改密码为更安全的值
-- 3. 执行此 SQL 前，请确保 user 表已经创建
-- 4. 此 SQL 适用于 MySQL 数据库

-- 初始化模型
-- 创建时间：2025-04-16 15:00:45

-- 添加钢构件锈蚀模型
INSERT INTO `model` (
    `model_name`,
    `model_path`,
    `disease_category`,
    `augmentation`,
    `layers`,
    `parameters`,
    `GFLOPs`,
    `box_p`,
    `box_r`,
    `box_mAP50`,
    `box_mAP50_95`,
    `mask_p`,
    `mask_r`,
    `mask_mAP50`,
    `mask_mAP50_95`,
    `f1_score`,
    `fitness_score`,
    `created_at`,
    `updated_at`,
    `owner_id`
) VALUES (
    'steel_corrosion.pt',
    'static\\models\\steel_corrosion.pt',
    '钢构件锈蚀',
    '随机点+颜色扭曲+高斯模糊',
    113,
    10070299,
    35.3,
    0.972,
    0.925,
    0.966,
    0.878,
    0.973,
    0.919,
    0.956,
    0.66,
    1.8931,
    1.57629,
    NOW(),
    NOW(),
    2
);

-- 添加钢构件涂层剥脱/鼓包模型
INSERT INTO `model` (
    `model_name`,
    `model_path`,
    `disease_category`,
    `augmentation`,
    `layers`,
    `parameters`,
    `GFLOPs`,
    `box_p`,
    `box_r`,
    `box_mAP50`,
    `box_mAP50_95`,
    `mask_p`,
    `mask_r`,
    `mask_mAP50`,
    `mask_mAP50_95`,
    `f1_score`,
    `fitness_score`,
    `created_at`,
    `updated_at`,
    `owner_id`
) VALUES (
    'steel_coating_peel_bubble.pt',
    'static\\models\\steel_coating_peel_bubble.pt',
    '钢构件涂层剥脱/鼓包',
    '随机点+颜色扭曲+高斯模糊',
    113,
    10070299,
    35.3,
    0.832,
    0.803,
    0.844,
    0.661,
    0.831,
    0.759,
    0.799,
    0.473,
    1.6103,
    1.18434,
    NOW(),
    NOW(),
    2
);

-- 添加混凝土剥落露筋模型
INSERT INTO `model` (
    `model_name`,
    `model_path`,
    `disease_category`,
    `augmentation`,
    `layers`,
    `parameters`,
    `GFLOPs`,
    `box_p`,
    `box_r`,
    `box_mAP50`,
    `box_mAP50_95`,
    `mask_p`,
    `mask_r`,
    `mask_mAP50`,
    `mask_mAP50_95`,
    `f1_score`,
    `fitness_score`,
    `created_at`,
    `updated_at`,
    `owner_id`
) VALUES (
    'concrete_peeling_rebar.pt',
    'static\\models\\concrete_peeling_rebar.pt',
    '混凝土剥落露筋',
    '随机点+颜色扭曲+高斯模糊',
    113,
    10070299,
    35.3,
    0.924,
    0.76,
    0.851,
    0.655,
    0.884,
    0.731,
    0.803,
    0.475,
    1.6338,
    1.18312,
    NOW(),
    NOW(),
    2
);

-- 添加钢构件裂缝模型
INSERT INTO `model` (
    `model_name`,
    `model_path`,
    `disease_category`,
    `augmentation`,
    `layers`,
    `parameters`,
    `GFLOPs`,
    `box_p`,
    `box_r`,
    `box_mAP50`,
    `box_mAP50_95`,
    `mask_p`,
    `mask_r`,
    `mask_mAP50`,
    `mask_mAP50_95`,
    `f1_score`,
    `fitness_score`,
    `created_at`,
    `updated_at`,
    `owner_id`
) VALUES (
    'steel_crack.pt',
    'static\\models\\steel_crack.pt',
    '钢构件裂缝',
    '随机点+颜色扭曲+高斯模糊',
    113,
    10070299,
    35.3,
    0.805,
    0.768,
    0.778,
    0.608,
    0.646,
    0.546,
    0.489,
    0.197,
    1.378,
    0.85097,
    NOW(),
    NOW(),
    2
);

-- 添加混凝土裂缝模型
INSERT INTO `model` (
    `model_name`,
    `model_path`,
    `disease_category`,
    `augmentation`,
    `layers`,
    `parameters`,
    `GFLOPs`,
    `box_p`,
    `box_r`,
    `box_mAP50`,
    `box_mAP50_95`,
    `mask_p`,
    `mask_r`,
    `mask_mAP50`,
    `mask_mAP50_95`,
    `f1_score`,
    `fitness_score`,
    `created_at`,
    `updated_at`,
    `owner_id`
) VALUES (
    'concrete_crack.pt',
    'static\\models\\concrete_crack.pt',
    '混凝土裂缝',
    '随机点+颜色扭曲+高斯模糊',
    113,
    10070299,
    35.3,
    0.909,
    0.89,
    0.941,
    0.771,
    0.759,
    0.628,
    0.615,
    0.197,
    1.5863,
    1.02686,
    NOW(),
    NOW(),
    2
);

-- 添加混凝土风化模型
INSERT INTO `model` (
    `model_name`,
    `model_path`,
    `disease_category`,
    `augmentation`,
    `layers`,
    `parameters`,
    `GFLOPs`,
    `box_p`,
    `box_r`,
    `box_mAP50`,
    `box_mAP50_95`,
    `mask_p`,
    `mask_r`,
    `mask_mAP50`,
    `mask_mAP50_95`,
    `f1_score`,
    `fitness_score`,
    `created_at`,
    `updated_at`,
    `owner_id`
) VALUES (
    'concrete_weathering.pt',
    'static\\models\\concrete_weathering.pt',
    '混凝土风化',
    '随机点+颜色扭曲+高斯模糊',
    113,
    10070299,
    35.3,
    0.884,
    0.737,
    0.804,
    0.634,
    0.87,
    0.72,
    0.782,
    0.476,
    1.5919,
    1.15776,
    NOW(),
    NOW(),
    2
);

-- 添加路面坑凼模型
INSERT INTO `model` (
    `model_name`,
    `model_path`,
    `disease_category`,
    `augmentation`,
    `layers`,
    `parameters`,
    `GFLOPs`,
    `box_p`,
    `box_r`,
    `box_mAP50`,
    `box_mAP50_95`,
    `mask_p`,
    `mask_r`,
    `mask_mAP50`,
    `mask_mAP50_95`,
    `f1_score`,
    `fitness_score`,
    `created_at`,
    `updated_at`,
    `owner_id`
) VALUES (
    'road_pothole.pt',
    'static\\models\\road_pothole.pt',
    '路面坑凼',
    '随机点+颜色扭曲+高斯模糊',
    113,
    10070299,
    35.3,
    0.954,
    0.935,
    0.973,
    0.809,
    0.958,
    0.931,
    0.973,
    0.735,
    1.8882,
    1.58462,
    NOW(),
    NOW(),
    2
);

-- 注意：
-- 1. 执行此 SQL 前，请确保 model 表已经创建
-- 2. 此 SQL 适用于 MySQL 数据库
-- 3. 所有模型均属于开发人员用户（user_id = 2）