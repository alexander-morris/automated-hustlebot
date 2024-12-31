import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    const disposable = vscode.commands.registerCommand('cursor.autoAccept', () => {
        // Auto-accept changes
        vscode.commands.executeCommand('cursor.acceptChange');
    });

    context.subscriptions.push(disposable);

    // Listen for change suggestions
    vscode.workspace.onDidChangeTextDocument(() => {
        vscode.commands.executeCommand('cursor.acceptChange');
    });
} 