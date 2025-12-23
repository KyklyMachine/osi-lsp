/**
 * VS Code Extension for OSI Protocol Language
 */

import * as path from 'path';
import { workspace, ExtensionContext, window } from 'vscode';
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
    TransportKind
} from 'vscode-languageclient/node';

let client: LanguageClient | undefined;

export function activate(context: ExtensionContext) {
    console.log('OSI Protocol Language Extension is now active');

    // Get Python path from configuration
    const config = workspace.getConfiguration('osiLanguageServer');
    let pythonPath = config.get<string>('pythonPath', 'python');

    // Check if a virtual environment exists in the server directory
    // If pythonPath is still default 'python', try to use the venv
    if (pythonPath === 'python') {
        const venvPythonPath = context.asAbsolutePath(
            path.join('..', 'server', 'venv', process.platform === 'win32' ? 'Scripts' : 'bin', process.platform === 'win32' ? 'python.exe' : 'python')
        );
        
        const fs = require('fs');
        if (fs.existsSync(venvPythonPath)) {
            pythonPath = venvPythonPath;
            console.log(`Using virtual environment Python: ${pythonPath}`);
        }
    }

    // Path to the language server module directory
    const serverDir = context.asAbsolutePath(
        path.join('..', 'server')
    );

    // Check if server file exists
    const fs = require('fs');
    // We check for the module file existence to be safe, though we run via -m
    const serverEntry = path.join(serverDir, 'osi_lsp', 'server.py');
    if (!fs.existsSync(serverEntry)) {
        window.showErrorMessage(
            `OSI Language Server not found at ${serverEntry}. ` +
            `Please ensure the server is installed correctly.`
        );
        return;
    }

    // Server options
    const serverOptions: ServerOptions = {
        command: pythonPath,
        args: ['-m', 'osi_lsp.server'],
        transport: TransportKind.stdio,
        options: {
            cwd: serverDir
        }
    };

    // Client options
    const clientOptions: LanguageClientOptions = {
        documentSelector: [
            { scheme: 'file', language: 'osi' }
        ],
        synchronize: {
            fileEvents: workspace.createFileSystemWatcher('**/*.osi')
        },
        outputChannelName: 'OSI Language Server'
    };

    // Create the language client
    client = new LanguageClient(
        'osiLanguageServer',
        'OSI Language Server',
        serverOptions,
        clientOptions
    );

    // Start the client (this will also launch the server)
    client.start().then(() => {
        console.log('OSI Language Server started');
    }).catch((error) => {
        window.showErrorMessage(
            `Failed to start OSI Language Server: ${error.message}`
        );
        console.error('Failed to start server:', error);
    });

    // Add client to subscriptions for cleanup
    context.subscriptions.push({
        dispose: () => {
            if (client) {
                client.stop();
            }
        }
    });
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined;
    }
    return client.stop();
}