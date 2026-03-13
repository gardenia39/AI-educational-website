# Django 电商项目结构说明（FootFusion）

```
Django-eCommerce-Website/
│
├── .env                        # 🔒 环境变量（密钥、数据库、邮箱密码等敏感配置）
├── .gitignore                  # Git 忽略规则
├── .gitattributes              # Git 属性配置
├── LICENSE                     # 开源许可证
├── README.md                   # 项目说明文档
├── manage.py                   # 🚀 Django 项目启动入口（运行服务器、迁移数据库等）
├── db.sqlite3                  # 📦 SQLite 数据库文件（存储所有数据）
├── requirements.txt            # 📋 项目依赖包列表（pip install -r requirements.txt）
│
├── ecomm/                      # ⚙️ 【项目配置】Django 项目核心配置
│   ├── __init__.py             #    包标识文件
│   ├── settings.py             #    ⭐ 全局设置（数据库、邮箱、中间件、第三方应用等）
│   ├── urls.py                 #    ⭐ 主路由（把 URL 分发到各个 app）
│   ├── wsgi.py                 #    生产部署入口（WSGI 协议）
│   └── asgi.py                 #    异步部署入口（ASGI 协议）
│
├── accounts/                   # 👤 【用户模块】用户相关功能
│   ├── __init__.py             #    包标识文件
│   ├── models.py               #    ⭐ 数据模型（用户资料 Profile、购物车 Cart、
│   │                           #       购物车商品 CartItem、订单 Order 等）
│   ├── views.py                #    ⭐ 视图逻辑（登录、注册、购物车操作、
│   │                           #       下单、个人资料、生成订单PDF等）
│   ├── urls.py                 #    URL 路由（/accounts/ 下的所有链接）
│   ├── admin.py                #    后台管理注册（让 Admin 后台能管理用户数据）
│   ├── forms.py                #    表单定义（用户资料编辑表单、地址表单）
│   ├── signals.py              #    信号（用户注册时自动创建 Profile）
│   ├── apps.py                 #    应用配置
│   ├── tests.py                #    测试文件
│   └── migrations/             #    数据库迁移文件（自动生成）
│
├── products/                   # 🛍️ 【商品模块】商品相关功能
│   ├── __init__.py             #    包标识文件
│   ├── models.py               #    ⭐ 数据模型（商品 Product、分类 Category、
│   │                           #       颜色 ColorVariant、尺寸 SizeVariant、
│   │                           #       商品图片、优惠券 Coupon、评价、收藏夹等）
│   ├── views.py                #    ⭐ 视图逻辑（商品列表、商品详情、
│   │                           #       收藏夹操作、评价提交等）
│   ├── urls.py                 #    URL 路由（/products/ 下的所有链接）
│   ├── admin.py                #    ⭐ 后台管理（在这里配置 Admin 后台如何
│   │                           #       显示和管理商品——添加商品就靠它！）
│   ├── forms.py                #    表单定义（评价表单等）
│   ├── apps.py                 #    应用配置
│   ├── tests.py                #    测试文件
│   └── migrations/             #    数据库迁移文件
│
├── home/                       # 🏠 【首页模块】首页和静态页面
│   ├── __init__.py             #    包标识文件
│   ├── models.py               #    数据模型（联系我们表单数据）
│   ├── views.py                #    视图逻辑（首页、搜索、关于、联系、隐私政策等）
│   ├── urls.py                 #    URL 路由
│   ├── admin.py                #    后台管理
│   ├── apps.py                 #    应用配置
│   ├── tests.py                #    测试文件
│   └── migrations/             #    数据库迁移文件
│
├── base/                       # 🧱 【基础模块】公共工具
│   ├── __init__.py             #    包标识文件
│   ├── models.py               #    基类模型（提供 uid、创建时间等公共字段）
│   └── emails.py               #    📧 邮件发送工具（发送验证邮件等）
│
├── templates/                  # 🎨 【前端模板】所有 HTML 页面
│   ├── 404.html                #    404 错误页面
│   ├── 500.html                #    500 错误页面
│   │
│   ├── base/                   #    基础模板
│   │   ├── base.html           #    ⭐ 主模板（所有页面的骨架，引入CSS/JS，
│   │   │                       #       顶部滚动条、导航栏、页脚）
│   │   └── alert.html          #    消息提示组件（成功/错误/警告弹窗）
│   │
│   ├── home/                   #    首页相关模板
│   │   ├── navbar.html         #    ⭐ 导航栏（菜单、搜索框、购物车图标）
│   │   ├── footer.html         #    页脚
│   │   ├── index.html          #    首页（商品展示）
│   │   ├── search.html         #    搜索结果页
│   │   ├── contact.html        #    联系我们页
│   │   ├── about.html          #    关于我们页
│   │   ├── privacy_policy.html #    隐私政策页
│   │   └── terms_and_conditions.html # 服务条款页
│   │
│   ├── accounts/               #    用户相关模板
│   │   ├── login.html          #    登录页
│   │   ├── register.html       #    注册页
│   │   ├── profile.html        #    个人资料页
│   │   ├── change_password.html#    修改密码页
│   │   ├── cart.html           #    购物车页
│   │   ├── order_history.html  #    订单历史页
│   │   ├── order_details.html  #    订单详情页
│   │   ├── order_pdf_generate.html # 订单 PDF 模板
│   │   └── shipping_address_form.html # 收货地址表单
│   │
│   ├── product/                #    商品相关模板
│   │   ├── product.html        #    商品详情页
│   │   ├── wishlist.html       #    收藏夹页
│   │   └── all_product_reviews.html # 所有评价页
│   │
│   ├── product_parts/          #    商品组件
│   │   └── product_list.html   #    商品列表卡片组件（被首页/搜索复用）
│   │
│   ├── emails/                 #    邮件模板
│   │   └── account_activation.html # 账号激活邮件
│   │
│   ├── payment_success/        #    支付相关
│   │   └── payment_success.html#    支付成功页
│   │
│   └── registration/           #    密码重置模板
│       ├── password_reset_form.html     # 输入邮箱
│       ├── password_reset_done.html     # 邮件已发送提示
│       ├── password_reset_confirm.html  # 设置新密码
│       ├── password_reset_complete.html # 重置完成
│       └── password_reset_email.html    # 重置密码邮件
│
├── public/media/               # 📁 【静态资源】CSS、JS、字体、图片
│   ├── css/                    #    样式文件
│   │   ├── bootstrap.css       #       Bootstrap 框架样式
│   │   ├── ui.css              #       自定义 UI 样式
│   │   ├── responsive.css      #       响应式样式
│   │   ├── footer.css          #       页脚样式
│   │   ├── register.css        #       登录注册样式
│   │   └── contact.css         #       联系页样式
│   ├── js/                     #    JavaScript 文件
│   │   └── script.js           #       自定义脚本
│   ├── fonts/                  #    字体文件（Font Awesome 图标等）
│   └── images/                 #    图片资源
│
├── Screenshots/                # 📸 项目截图（README 用）
└── venv/                       # 🐍 Python 虚拟环境（不要修改）
```

## 关键文件速查

| 你想做什么 | 去改哪个文件 |
|-----------|------------|
| 添加商品 | 访问 `http://127.0.0.1:8000/admin/` 后台 |
| 改页面文字/布局 | `templates/` 目录下的 `.html` 文件 |
| 改业务逻辑 | 各 app 下的 `views.py` |
| 改数据结构 | 各 app 下的 `models.py` |
| 改后台管理显示 | 各 app 下的 `admin.py` |
| 改 URL 路径 | 各 app 下的 `urls.py` |
| 改全局配置 | `ecomm/settings.py` |
| 改环境变量 | `.env` |
| 改样式 | `public/media/css/` 下的 CSS 文件 |
