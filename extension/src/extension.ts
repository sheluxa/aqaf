
import * as vscode from 'vscode';
import { callApi } from './apiClient';

export function activate(context: vscode.ExtensionContext) {
  const disposable = vscode.commands.registerCommand('aqa.generateFromSelection', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) { return; }
    const selection = editor.document.getText(editor.selection) || editor.document.getText();
    if (!selection) {
      vscode.window.showWarningMessage('Нет текста для генерации. Выделите описание теста.');
      return;
    }
    try {
      const testcase = await callApi('/generate/testcase', { prompt: selection, push_to_qase: false });
      const autotest = await callApi('/generate/autotest', { testcase_text: testcase.testcase });
      const doc = await vscode.workspace.openTextDocument({ language: 'typescript', content: autotest.code });
      vscode.window.showTextDocument(doc, { preview: false });
    } catch (e: any) {
      vscode.window.showErrorMessage(`Ошибка генерации: ${e?.message || e}`);
    }
  });
  context.subscriptions.push(disposable);
}

export function deactivate() {}
