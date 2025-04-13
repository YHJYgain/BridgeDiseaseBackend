# 桥梁病害检测系统传统 ER 图

<svg width="800" height="800" xmlns="http://www.w3.org/2000/svg">
  <!-- 背景 -->
  <rect width="800" height="800" fill="white"/>
  <!-- 实体：用户 -->
  <rect x="350" y="50" width="100" height="50" stroke="black" fill="white" stroke-width="2"/>
  <text x="400" y="80" text-anchor="middle" font-family="Arial" font-size="16">用户</text>
  <!-- 用户属性 -->
  <ellipse cx="200" cy="50" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="200" y="55" text-anchor="middle" font-family="Arial" font-size="14">用户ID</text>
  <ellipse cx="270" cy="30" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="270" y="35" text-anchor="middle" font-family="Arial" font-size="14">用户名</text>
  <ellipse cx="340" cy="10" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="340" y="15" text-anchor="middle" font-family="Arial" font-size="4">邮箱</text>
  <ellipse cx="460" cy="10" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="460" y="15" text-anchor="middle" font-family="Arial" font-size="14">密码</text>

  <ellipse cx="530" cy="30" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="530" y="35" text-anchor="middle" font-family="Arial" font-size="14">角色</text>

  <ellipse cx="600" cy="50" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="600" y="55" text-anchor="middle" font-family="Arial" font-size="14">电话</text>

  <!-- 连接用户与属性 -->
  <line x1="350" y1="75" x2="240" y2="50" stroke="black" stroke-width="1"/>
  <line x1="350" y1="70" x2="270" y2="30" stroke="black" stroke-width="1"/>
  <line x1="350" y1="65" x2="340" y2="10" stroke="black" stroke-width="1"/>
  <line x1="450" y1="65" x2="460" y2="10" stroke="black" stroke-width="1"/>
  <line x1="450" y1="70" x2="530" y2="30" stroke="black" stroke-width="1"/>
  <line x1="450" y1="75" x2="560" y2="50" stroke="black" stroke-width="1"/>

  <!-- 关系：拥有（用户-模型） -->
  <polygon points="400,150 380,170 400,190 420,170" stroke="black" fill="white" stroke-width="2"/>
  <text x="400" y="175" text-anchor="middle" font-family="Arial" font-size="14">拥有</text>

  <!-- 实体：模型 -->
  <rect x="350" y="240" width="100" height="50" stroke="black" fill="white" stroke-width="2"/>
  <text x="400" y="270" text-anchor="middle" font-family="Arial" font-size="16">模型</text>

  <!-- 模型属性 -->
  <ellipse cx="250" cy="240" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="250" y="245" text-anchor="middle" font-family="Arial" font-size="14">模型ID</text>

  <ellipse cx="300" cy="200" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="300" y="205" text-anchor="middle" font-family="Arial" font-size="14">模型名称</text>

  <ellipse cx="500" cy="200" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="500" y="205" text-anchor="middle" font-family="Arial" font-size="14">模型路径</text>

  <ellipse cx="550" cy="240" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="550" y="245" text-anchor="middle" font-family="Arial" font-size="14">病害类别</text>

  <!-- 连接模型与属性 -->
  <line x1="350" y1="265" x2="290" y2="240" stroke="black" stroke-width="1"/>
  <line x1="350" y1="255" x2="300" y2="200" stroke="black" stroke-width="1"/>
  <line x1="450" y1="255" x2="500" y2="200" stroke="black" stroke-width="1"/>
  <line x1="450" y1="265" x2="510" y2="240" stroke="black" stroke-width="1"/>

  <!-- 关系：执行（用户-检测） -->
  <polygon points="250,170 230,190 250,210 270,190" stroke="black" fill="white" stroke-width="2"/>
  <text x="250" y="195" text-anchor="middle" font-family="Arial" font-size="14">执行</text>

  <!-- 实体：检测 -->
  <rect x="200" y="320" width="100" height="50" stroke="black" fill="white" stroke-width="2"/>
  <text x="250" y="350" text-anchor="middle" font-family="Arial" font-size="16">检测</text>

  <!-- 检测属性 -->
  <ellipse cx="120" cy="300" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="120" y="305" text-anchor="middle" font-family="Arial" font-size="14">检测ID</text>
  <ellipse cx="150" cy="350" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="150" y="355" text-anchor="middle" font-family="Arial" font-size="14">结果路径</text>
  <ellipse cx="120" cy="400" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="120" y="405" text-anchor="middle" font-family="Arial" font-size="14">病害数量</text>
  <ellipse cx="200" cy="430" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="200" y="435" text-anchor="middle" font-family="Arial" font-size="14">病害面积</text>
  <ellipse cx="280" cy="430" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="280" y="435" text-anchor="middle" font-family="Arial" font-size="14">病害等级</text>
  <ellipse cx="350" cy="400" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="350" y="405" text-anchor="middle" font-family="Arial" font-size="14">检测状态</text>

  <!-- 连接检测与属性 -->
  <line x1="200" y1="330" x2="160" y2="300" stroke="black" stroke-width="1"/>
  <line x1="200" y1="350" x2="190" y2="350" stroke="black" stroke-width="1"/>
  <line x1="200" y1="370" x2="160" y2="400" stroke="black" stroke-width="1"/>
  <line x1="250" y1="370" x2="200" y2="430" stroke="black" stroke-width="1"/>
  <line x1="300" y1="370" x2="280" y2="430" stroke="black" stroke-width="1"/>
  <line x1="300" y1="345" x2="350" y2="400" stroke="black" stroke-width="1"/>

  <!-- 关系：用于（模型-检测） -->
  <polygon points="320,320 300,340 320,360 340,340" stroke="black" fill="white" stroke-width="2"/>
  <text x="320" y="345" text-anchor="middle" font-family="Arial" font-size="14">用于</text>

  <!-- 关系：拥有（用户-媒体） -->
  <polygon points="550,170 530,190 550,210 570,190" stroke="black" fill="white" stroke-width="2"/>
  <text x="550" y="195" text-anchor="middle" font-family="Arial" font-size="14">拥有</text>

  <!-- 实体：媒体 -->
  <rect x="500" y="320" width="100" height="50" stroke="black" fill="white" stroke-width="2"/>
  <text x="550" y="350" text-anchor="middle" font-family="Arial" font-size="16">媒体</text>

  <!-- 媒体属性 -->
  <ellipse cx="450" cy="300" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="450" y="305" text-anchor="middle" font-family="Arial" font-size="14">媒体ID</text>
  <ellipse cx="650" cy="300" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="650" y="305" text-anchor="middle" font-family="Arial" font-size="14">媒体名称</text>
  <ellipse cx="680" cy="350" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="680" y="355" text-anchor="middle" font-family="Arial" font-size="14">媒体路径</text>
  <ellipse cx="650" cy="400" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="650" y="405" text-anchor="middle" font-family="Arial" font-size="14">文件类型</text>
  <ellipse cx="550" cy="430" rx="40" ry="25" stroke="black" fill="white" stroke-width="2"/>
  <text x="550" y="435" text-anchor="middle" font-family="Arial" font-size="14">分辨率</text>

  <!-- 连接媒体与属性 -->
  <line x1="500" y1="330" x2="450" y2="300" stroke="black" stroke-width="1"/>
  <line x1="600" y1="330" x2="650" y2="300" stroke="black" stroke-width="1"/>
  <line x1="600" y1="345" x2="680" y2="350" stroke="black" stroke-width="1"/>
  <line x1="600" y1="370" x2="650" y2="400" stroke="black" stroke-width="1"/>
  <line x1="550" y1="370" x2="550" y2="430" stroke="black" stroke-width="1"/>

  <!-- 关系：用于（媒体-检测） -->
  <polygon points="400,370 380,390 400,410 420,390" stroke="black" fill="white" stroke-width="2"/>
  <text x="400" y="395" text-anchor="middle" font-family="Arial" font-size="14">用于</text>

  <!-- 连接关系 -->
  <!-- 用户-拥有-模型 -->
  <line x1="400" y1="100" x2="400" y2="150" stroke="black" stroke-width="1"/>
  <text x="410" y="125" text-anchor="middle" font-family="Arial" font-size="12">1</text>
  <line x1="400" y1="190" x2="400" y2="240" stroke="black" stroke-width="1"/>
  <text x="410" y="215" text-anchor="middle" font-family="Arial" font-size="12">n</text>

  <!-- 用户-执行-检测 -->
  <line x1="350" y1="75" x2="250" y2="170" stroke="black" stroke-width="1"/>
  <text x="290" y="120" text-anchor="middle" font-family="Arial" font-size="12">1</text>
  <line x1="250" y1="210" x2="250" y2="320" stroke="black" stroke-width="1"/>
  <text x="260" y="265" text-anchor="middle" font-family="Arial" font-size="12">n</text>

  <!-- 用户-拥有-媒体 -->
  <line x1="450" y1="75" x2="550" y2="170" stroke="black" stroke-width="1"/>
  <text x="510" y="120" text-anchor="middle" font-family="Arial" font-size="12">1</text>
  <line x1="550" y1="210" x2="550" y2="320" stroke="black" stroke-width="1"/>
  <text x="560" y="265" text-anchor="middle" font-family="Arial" font-size="12">n</text>

  <!-- 模型-用于-检测 -->
  <line x1="350" y1="290" x2="320" y2="320" stroke="black" stroke-width="1"/>
  <text x="330" y="300" text-anchor="middle" font-family="Arial" font-size="12">1</text>
  <line x1="320" y1="360" x2="300" y2="370" stroke="black" stroke-width="1"/>
  <text x="310" y="370" text-anchor="middle" font-family="Arial" font-size="12">n</text>

  <!-- 媒体-用于-检测 -->
  <line x1="500" y1="370" x2="420" y2="390" stroke="black" stroke-width="1"/>
  <text x="450" y="375" text-anchor="middle" font-family="Arial" font-size="12">1</text>
  <line x1="380" y1="390" x2="300" y2="370" stroke="black" stroke-width="1"/>
  <text x="340" y="375" text-anchor="middle" font-family="Arial" font-size="12">n</text>
</svg>
