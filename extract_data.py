from search_strategy_table_extractor import read_search_strategy_tables
from quality_assessment_table_extractor import read_quality_assessment_table

base_dir = './data'
read_num, has_quality_assessment_num = read_quality_assessment_table(base_dir)
total_num, has_search_strategy_num = read_search_strategy_tables(base_dir)

print(f"total number of read articles is {read_num}")
print(f"total number of read articles that has quality assessment table is {has_quality_assessment_num}")
print(f"total number of read articles that has search strategy table is {has_search_strategy_num}")
print(total_num)
