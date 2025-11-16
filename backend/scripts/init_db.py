"""
数据库初始化脚本

手动运行此脚本来初始化数据库表结构。
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import init_db, engine
from app.models import Base


def main():
    """初始化数据库"""
    print("🔧 开始初始化数据库...")
    
    try:
        # 创建所有表
        init_db()
        
        # 验证表是否创建成功
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"✅ 数据库初始化成功！")
        print(f"📊 已创建的表: {', '.join(tables)}")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()