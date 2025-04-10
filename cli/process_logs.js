#!/usr/bin/env node

const readline = require('readline')

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
})

function stripAnsi(str) {
    // 移除所有 ANSI 转义序列
    return str.replace(/\u001b\[\d+m/g, '')
}

function processLogLine(line) {
    // 提取 INFO {...} 部分
    if (!line.includes('INFO  {')) {
        return
    }

    const start = line.indexOf('{')
    const end = line.lastIndexOf('}') + 1
    let objStr = line.substring(start, end)

    // 清理 ANSI 转义序列
    objStr = stripAnsi(objStr)

    try {
        // 直接用 eval 解析 JavaScript 对象
        // eslint-disable-next-line no-eval
        const data = eval('(' + objStr + ')')

        if (data.data) {
            process.stdout.write(data.data)
        }
    } catch (e) {
        console.error('Error processing line:', e.message)
        console.error('Cleaned object string:', objStr)
    }
}

rl.on('line', (line) => {
    processLogLine(line.trim())
})
