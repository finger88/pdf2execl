import pdfplumber
import pandas as pd
import os

def extract_and_merge_tables(pdf_path, output_path):
    # 从PDF中提取所有表格
    print(f"正在从{pdf_path}中提取表格...")
    all_tables = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    # 将表格转换为DataFrame
                    df = pd.DataFrame(table[1:], columns=table[0])
                    all_tables.append(df)
    
    if not all_tables:
        print("未找到任何表格！")
        return
    
    print(f"共找到{len(all_tables)}个表格")
    
    # 合并所有表格
    merged_df = pd.concat(all_tables, ignore_index=True)
    
    # 删除完全重复的行
    merged_df = merged_df.drop_duplicates()
    
    # 保存到Excel文件
    print(f"正在保存合并后的表格到{output_path}...")
    merged_df.to_excel(output_path, index=False)
    print("处理完成！")

def main():
    # 获取当前目录下的PDF文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_files = [f for f in os.listdir(current_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("当前目录下没有找到PDF文件！")
        return
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(current_dir, pdf_file)
        output_path = os.path.join(current_dir, f"{os.path.splitext(pdf_file)[0]}_merged.xlsx")
        
        try:
            extract_and_merge_tables(pdf_path, output_path)
        except Exception as e:
            print(f"处理{pdf_file}时发生错误：{str(e)}")

if __name__ == '__main__':
    main()