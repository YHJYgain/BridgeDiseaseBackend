# 桥梁病害检测系统传统ER图

```mermaid
graph LR
    %% 实体定义 - 矩形
    USER[用户]
    MODEL[模型]
    MEDIA[媒体]
    DETECTION[检测]
    OPERATION[操作]
    
    %% 关系定义 - 菱形
    OWNS1{拥有}
    OWNS2{拥有}
    PERFORMS1{执行}
    PERFORMS2{执行}
    USED_IN1{用于}
    USED_IN2{用于}
    
    %% 用户属性 - 椭圆
    USERNAME((用户名))
    EMAIL((邮箱))
    PASSWORD((密码))
    ROLE((角色))
    
    %% 模型属性 - 椭圆
    MODEL_NAME((模型名称))
    DISEASE_CATEGORY((病害类别))
    AUGMENTATION((数据增强方式))
    FITNESS_SCORE((适应度分数))
    
    %% 媒体属性 - 椭圆
    MEDIA_NAME((媒体名称))
    FILE_TYPE((文件类型))
    FRAME_COUNT((帧数))
    
    %% 检测属性 - 椭圆
    DISEASE_SEVERITY_SCORE((病害严重性得分))
    DISEASE_GRADE((病害等级))
    DISEASE_DESCRIPTION((病害评估描述))
    DETECTION_DURATION((检测分割耗时))
    AVG_FRAME_DETECTION_DURATION((帧平均检测分割耗时))
    DETECTION_STATUS((检测状态))
    
    %% 操作属性 - 椭圆
    OPERATION_TYPE((操作类型))
    OP_DESCRIPTION((操作描述))
    DURATION((耗时))
    
    %% 实体与属性的连接
    USER --- USERNAME
    USER --- EMAIL
    USER --- PASSWORD
    USER --- ROLE
    
    MODEL --- MODEL_NAME
    MODEL --- DISEASE_CATEGORY
    MODEL --- AUGMENTATION
    MODEL --- FITNESS_SCORE
    
    MEDIA --- MEDIA_NAME
    MEDIA --- FILE_TYPE
    MEDIA --- FRAME_COUNT
    
    DETECTION --- DISEASE_SEVERITY_SCORE
    DETECTION --- DISEASE_GRADE
    DETECTION --- DISEASE_DESCRIPTION
    DETECTION --- DETECTION_DURATION
    DETECTION --- AVG_FRAME_DETECTION_DURATION
    DETECTION --- DETECTION_STATUS
    
    OPERATION --- OPERATION_TYPE
    OPERATION --- OP_DESCRIPTION
    OPERATION --- DURATION
    USER -->|1| OWNS1
    OWNS1 -->|n| MODEL
    USER -->|1| OWNS2
    OWNS2 -->|n| MEDIA
    USER -->|1| PERFORMS1
    PERFORMS1 -->|n| DETECTION
    USER -->|1| PERFORMS2
    PERFORMS2 -->|n| OPERATION
    MODEL -->|1| USED_IN1
    USED_IN1 -->|n| DETECTION
    MEDIA -->|1| USED_IN2
    USED_IN2 -->|n| DETECTION
```

## 实体说明

### 用户 (User)
- 存储用户的基本信息，包括用户名、邮箱、密码等
- 用户角色分为管理员(ADMIN)、开发者(DEVELOPER)和普通用户(USER)
- 用户状态包括活跃(ACTIVE)、非活跃(INACTIVE)和禁用(BANNED)

### 模型 (Model)
- 存储不同训练模型的基本信息和性能评估指标
- 包含模型名称、存储路径、病害类别、数据增强方式等
- 记录模型的性能指标，如精度、召回率、F1分数等

### 媒体 (Media)
- 存储与用户相关联的媒体文件信息
- 包含文件名、路径、类型、分辨率等
- 媒体可以是图片或视频

### 检测 (Detection)
- 每条记录对应一次检测任务
- 包含检测结果路径及相关统计信息
- 记录病害数量、面积、形状复杂度等评估指标
- 任务状态包括待处理(PENDING)、处理中(IN_PROGRESS)、已完成(COMPLETED)和失败(FAILED)

### 操作 (Operation)
- 记录系统中的各种操作，用于审计和监控
- 包含操作类型、描述、耗时、状态等
- 操作类型包括认证(AUTHENTICATE)、创建(CREATE)、读取(READ)、更新(UPDATE)和删除(DELETE)
- 操作状态包括成功(SUCCESS)和失败(FAILURE)