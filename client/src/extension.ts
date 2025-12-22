/**
 * VS Code Extension for Protocol Language
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
    console.log('Protocol Language Extension is now active');

    // Get Python path from configuration
    const config = workspace.getConfiguration('protocolLanguageServer');
    const pythonPath = config.get<string>('pythonPath', 'python');

    // Path to the language server
    const serverPath = context.asAbsolutePath(
        path.join('..', 'server', 'protocol_ls', 'server.py')
    );

    // Check if server file exists
    const fs = require('fs');
    if (!fs.existsSync(serverPath)) {
        window.showErrorMessage(
            `Protocol Language Server not found at ${serverPath}. ` +
            `Please ensure the server is installed correctly.`
        );
        return;
    }

    // Server options
    const serverOptions: ServerOptions = {
        command: pythonPath,
        args: [serverPath],
        transport: TransportKind.stdio,
        options: {
            cwd: path.dirname(serverPath)
        }
    };

    // Client options
    const clientOptions: LanguageClientOptions = {
        documentSelector: [
            { scheme: 'file', language: 'protocol' }
        ],
        synchronize: {
            fileEvents: workspace.createFileSystemWatcher('**/*.{protocol,prot}')
        },
        outputChannelName: 'Protocol Language Server'
    };

    // Create the language client
    client = new LanguageClient(
        'protocolLanguageServer',
        'Protocol Language Server',
        serverOptions,
        clientOptions
    );

    // Start the client (this will also launch the server)
    client.start().then(() => {
        console.log('Protocol Language Server started');
    }).catch((error) => {
        window.showErrorMessage(
            `Failed to start Protocol Language Server: ${error.message}`
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
