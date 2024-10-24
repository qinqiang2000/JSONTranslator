def generate_table(data, name):
    html = f'''
    <div class="ui-card ui-card-bordered ui-card-small pui-pages-shared-doc-http-api-index-parameters__card pui-pages-shared-doc-http-api-index-parameters__classic">
        <div class="ui-card-head">
            <div class="ui-card-head-wrapper">
                <div class="ui-card-head-title" style="font-size:20">{name}</div>
            </div>
        </div>
        <div class="ui-card-body">
            <div class="app-json-schema-viewer index_schema-viewer__i2ykd">
                <div class="" id="mosaic-provider-react-aria-0-1">
                    <div data-overlay-container="true" class="">
                        <div class="JsonSchemaViewer">
                            <div></div>
                            <div data-level="0" class="sl-text-sm">
                                <div class="sl-flex sl-px-3 sl-text-lg sl-py-1"
                                    style="font-size:16; color: var(--ui-table-header-color); border-bottom: var(--ui-border-width-base) var(--ui-border-style-base) var(--ui-table-border-color);">
                                    <div style="width: 200px;">枚举值</div>
                                    <div class="sl-flex-1">说明</div>
                                </div>
                                <div class="" style="margin-left: 0px;">
    '''

    # 遍历 data (即 enumDescriptions)
    for enum_value, description in data.items():
        html += f'''
            <div data-id="{enum_value}" class="index_node__G6-Qx index_node__classic__TXhTT sl-relative sl-max-w-full"
                style="border-bottom: var(--ui-border-width-base) var(--ui-border-style-base) var(--ui-table-border-color); padding-top: 5px; padding-bottom: 5px;">
                <div class="sl-flex sl-relative sl-w-full sl-pr-3 sl-pl-3">
                    <div class="sl-flex sl-flex-1 sl-flex-col sl-items-stretch sl-max-w-full" style="gap: 4px;">
                        <div class="sl-flex">
                            <div class="sl-flex sl-items-start" style="width: 200px;">
                                <div style="word-break: break-word;">
                                    <div class="sl-flex">
                                        <span class="">
                                            <div class="PropertyNameRender_propertyName__3nXIr">
                                                <span style="font-size:13" class="pui-g-ui-kit-copyable-text-kit-index-copyable">{enum_value}</span>
                                            </div>
                                        </span>
                                    </div>
                                </div>
                                <div></div>
                            </div>
                            <div class="sl-flex-1">
                                <div style="margin-top: -4px;">
                                    <span class="break-all">
                                        <div class="json-schema-viewer__description" style="margin-left: 0px; margin-top: 6px;">
                                            <div class="markdown-body remark-mdx">
                                                <p style="font-size:13" data-first="true" data-last="true">{description}</p>
                                            </div>
                                        </div>
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        '''

    html += '''
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''

    return html


def generate_enum_html_v2(enum_data):
    if not enum_data or len(enum_data) < 1:
        return None

    _html = '<h3 class="pui-pages-shared-doc-http-api-index-content__title">枚举值</h3> <div id="piaozone_enum" class="group-content">'

    for e in enum_data:
        _html += generate_table(e['enumDescriptions'], e['name'])

    _html += '</div>'

    return _html
