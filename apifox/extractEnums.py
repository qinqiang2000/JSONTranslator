def remove_duplicates(enum_data):
    unique_tables = []

    for value in enum_data:
        if not any(t['name'] == value['name'] and t['enumDescriptions'] == value['enumDescriptions'] for t in
                   unique_tables):
            unique_tables.append(value)

    return unique_tables


def extract_enums(api_schema, api_id):
    enum_data = []

    # 递归查找 API 对象
    def find_api_obj(items):
        for item in items:
            if 'api' in item and item['api'].get('id') == api_id:
                return item['api']
            if 'items' in item:
                result = find_api_obj(item['items'])
                if result:
                    return result
        return None

    # 递归查找 schemaCollection 中 id 匹配的对象
    def find_enum_descriptions_by_ref(ref_value):
        def recursive_find(items):
            for item in items:
                if item.get('id') == ref_value:
                    return item  # 返回整个对象
                if 'items' in item:
                    result = recursive_find(item['items'])
                    if result:
                        return result
            return None

        return recursive_find(api_schema.get('schemaCollection', []))

    # 递归遍历 'api' 对象的所有子对象，提取符合条件的枚举值
    def find_enums(obj):
        if isinstance(obj, dict):
            # 检查是否包含 "enum" 和 "x-apifox-enum" 或 "$ref"
            if 'enum' in obj:
                if 'x-apifox-enum' in obj:
                    name = obj.get('title') or obj.get('description') or 'Unknown Name'
                    enumDescriptions = {enum_item['value']: enum_item['description'] for enum_item in obj['x-apifox-enum']}
                    enum_data.append({
                        'name': name,
                        'enumDescriptions': enumDescriptions
                    })
                elif 'x-apifox' in obj and 'enumDescriptions' in obj['x-apifox']:
                    name = obj.get('title') or obj.get('description') or 'Unknown Name'
                    enumDescriptions = obj['x-apifox']['enumDescriptions']
                    enum_data.append({
                        'name': name,
                        'enumDescriptions': enumDescriptions
                    })
            elif '$ref' in obj:
                # 处理 $ref 引用
                ref_object = find_enum_descriptions_by_ref(obj['$ref'])  # 查找引用的对象
                if ref_object:
                    find_enums(ref_object)  # 递归调用 find_enums 处理引用的对象

            # 递归查找子对象
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    find_enums(value)
        elif isinstance(obj, list):
            for item in obj:
                find_enums(item)

    # 查找 API 对象
    api_obj = find_api_obj(api_schema['apiCollection'])
    if api_obj:
        find_enums(api_obj)

    # print(f"去重前的数据size: {len(enum_data)}")
    return remove_duplicates(enum_data)
    # return enum_data
