// lib/features/profile/presentation/screens/kyc_screen.dart
// ═══════════════════════════════════════════════════════════════

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import 'package:sen_parcelle/core/theme/app_theme.dart';
import 'package:sen_parcelle/shared/widgets/gradient_button.dart';
// import 'package:sen_parcelle/features/profile/presentation/providers/kyc_provider.dart';

// ─── État KYC ───
enum KYCStep { info, upload, pending }

class KYCNotifier extends StateNotifier<KYCStep> {
  KYCNotifier() : super(KYCStep.info);
  void goToUpload() => state = KYCStep.upload;
  void goToPending() => state = KYCStep.pending;
}

final kycProvider = StateNotifierProvider<KYCNotifier, KYCStep>(
  (ref) => KYCNotifier(),
);

class KYCScreen extends ConsumerStatefulWidget {
  const KYCScreen({super.key});
  @override ConsumerState<KYCScreen> createState() => _KYCScreenState();
}

class _KYCScreenState extends ConsumerState<KYCScreen> {
  String   _docType     = 'cni';
  String?  _fileName;
  bool     _isLoading   = false;

  static const _docTypes = [
    ('cni',       '🪪 Carte Nationale d\'Identité'),
    ('passeport', '📘 Passeport'),
    ('permis',    '🚗 Permis de conduire'),
  ];

  Future<void> _pickDocument() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'jpg', 'jpeg', 'png'],
    );
    if (result != null) {
      setState(() => _fileName = result.files.single.name);
    }
  }

  Future<void> _submit() async {
    if (_fileName == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Veuillez sélectionner un document')),
      );
      return;
    }
    setState(() => _isLoading = true);
    await Future.delayed(const Duration(seconds: 2)); // Simuler upload
    setState(() => _isLoading = false);
    ref.read(kycProvider.notifier).goToPending();
  }

  @override
  Widget build(BuildContext context) {
    final step = ref.watch(kycProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Vérification d\'identité')),
      body: switch (step) {
        KYCStep.info    => _InfoView(onStart: () => ref.read(kycProvider.notifier).goToUpload()),
        KYCStep.upload  => _UploadView(
            docType:   _docType,
            fileName:  _fileName,
            isLoading: _isLoading,
            onDocTypeChanged: (t) => setState(() => _docType = t),
            onPickFile: _pickDocument,
            onSubmit:  _submit,
            docTypes:  _docTypes,
          ),
        KYCStep.pending => const _PendingView(),
      },
    );
  }
}

class _InfoView extends StatelessWidget {
  final VoidCallback onStart;
  const _InfoView({required this.onStart});

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.all(24),
    child: Column(children: [
      const SizedBox(height: 32),
      Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          gradient: const LinearGradient(colors: [AppTheme.greenDark, AppTheme.green]),
          borderRadius: BorderRadius.circular(20),
        ),
        child: const Column(children: [
          Text('🔐', style: TextStyle(fontSize: 52)),
          SizedBox(height: 12),
          Text('Vérification KYC', textAlign: TextAlign.center,
            style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
          SizedBox(height: 8),
          Text(
            'Pour publier des parcelles et effectuer des transactions, '
            'votre identité doit être vérifiée.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.white70, fontSize: 13, height: 1.5),
          ),
        ]),
      ),
      const SizedBox(height: 32),
      ...[
        ('1', 'Choisissez un document', 'CNI, passeport ou permis'),
        ('2', 'Uploadez le document',   'Format PDF, JPG ou PNG — Max 10MB'),
        ('3', 'Attendez la validation', 'Réponse sous 24h par SMS'),
      ].map((s) => Padding(
        padding: const EdgeInsets.only(bottom: 14),
        child: Row(children: [
          CircleAvatar(
            backgroundColor: AppTheme.greenLight,
            child: Text(s.$1, style: const TextStyle(
              color: AppTheme.green, fontWeight: FontWeight.bold)),
          ),
          const SizedBox(width: 14),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(s.$2, style: const TextStyle(fontWeight: FontWeight.w600)),
            Text(s.$3, style: const TextStyle(color: AppTheme.muted, fontSize: 12)),
          ]),
        ]),
      )),
      const Spacer(),
      GradientButton(label: 'Commencer la vérification', onPressed: onStart),
    ]),
  );
}

class _UploadView extends StatelessWidget {
  final String   docType;
  final String?  fileName;
  final bool     isLoading;
  final void Function(String) onDocTypeChanged;
  final VoidCallback onPickFile;
  final VoidCallback onSubmit;
  final List<(String, String)> docTypes;

  const _UploadView({
    required this.docType,     required this.fileName,
    required this.isLoading,   required this.onDocTypeChanged,
    required this.onPickFile,  required this.onSubmit,
    required this.docTypes,
  });

  @override
  Widget build(BuildContext context) => SingleChildScrollView(
    padding: const EdgeInsets.all(24),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('Type de document', style: Theme.of(context).textTheme.titleMedium),
      const SizedBox(height: 12),
      ...docTypes.map((t) => RadioListTile<String>(
        value: t.$1, groupValue: docType,
        title: Text(t.$2),
        activeColor: AppTheme.green,
        onChanged: (v) => onDocTypeChanged(v!),
        contentPadding: EdgeInsets.zero,
      )),
      const SizedBox(height: 20),
      Text('Document', style: Theme.of(context).textTheme.titleMedium),
      const SizedBox(height: 12),
      GestureDetector(
        onTap: onPickFile,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: fileName != null ? AppTheme.greenBg : AppTheme.bgLight,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: fileName != null ? AppTheme.green : Colors.grey.shade300,
              width: 1.5,
              style: BorderStyle.solid,
            ),
          ),
          child: Column(children: [
            Text(fileName != null ? '✅' : '📁',
              style: const TextStyle(fontSize: 36)),
            const SizedBox(height: 8),
            Text(
              fileName ?? 'Appuyer pour sélectionner',
              style: TextStyle(
                fontWeight: FontWeight.w600,
                color: fileName != null ? AppTheme.green : AppTheme.muted,
              ),
              textAlign: TextAlign.center,
              maxLines: 2, overflow: TextOverflow.ellipsis,
            ),
            if (fileName == null) ...[
              const SizedBox(height: 4),
              const Text('PDF, JPG, PNG — Max 10MB',
                style: TextStyle(color: AppTheme.muted, fontSize: 12)),
            ],
          ]),
        ),
      ),
      const SizedBox(height: 16),
      Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.amber.shade50,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: Colors.amber.shade200),
        ),
        child: const Row(children: [
          Text('⚠️ '),
          Expanded(child: Text(
            'Vos documents sont chiffrés et stockés de façon sécurisée. '
            'Ils ne sont accessibles que par nos administrateurs.',
            style: TextStyle(fontSize: 12, color: AppTheme.slate),
          )),
        ]),
      ),
      const SizedBox(height: 24),
      GradientButton(
        label: 'Envoyer mes documents',
        isLoading: isLoading,
        onPressed: onSubmit,
      ),
    ]),
  );
}

class _PendingView extends StatelessWidget {
  const _PendingView();
  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(32),
      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        const Text('⏳', style: TextStyle(fontSize: 72)),
        const SizedBox(height: 20),
        Text('Documents soumis !',
          style: Theme.of(context).textTheme.headlineMedium,
          textAlign: TextAlign.center),
        const SizedBox(height: 12),
        const Text(
          'Votre dossier est en cours de vérification.\n'
          'Vous recevrez une notification SMS sous 24h.',
          textAlign: TextAlign.center,
          style: TextStyle(color: AppTheme.muted, height: 1.6),
        ),
        const SizedBox(height: 32),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppTheme.greenBg,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppTheme.greenLight),
          ),
          child: const Column(children: [
            Row(children: [
              Icon(Icons.check_circle, color: AppTheme.green, size: 18),
              SizedBox(width: 8),
              Text('Document reçu et chiffré', style: TextStyle(fontWeight: FontWeight.w600)),
            ]),
            SizedBox(height: 8),
            Row(children: [
              Icon(Icons.schedule, color: AppTheme.amber, size: 18),
              SizedBox(width: 8),
              Text('Vérification en cours (< 24h)', style: TextStyle(fontWeight: FontWeight.w600)),
            ]),
          ]),
        ),
      ]),
    ),
  );
}


// ═══════════════════════════════════════════════════════════════