import 'dart:convert';
import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/api_exception.dart';
import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/fashion_ui.dart';
import '../../cart/presentation/cart_screen.dart';
import '../../catalog/data/catalog_models.dart';
import '../../reservations/presentation/reservations_screen.dart';

class VirtualFittingScreen extends ConsumerStatefulWidget {
  const VirtualFittingScreen({
    super.key,
    required this.productId,
    required this.productName,
    this.imageUrl,
    this.price,
    this.pickImageFromGallery,
  });

  final int productId;
  final String productName;
  final String? imageUrl;
  final double? price;

  @visibleForTesting
  final Future<XFile?> Function()? pickImageFromGallery;

  @override
  ConsumerState<VirtualFittingScreen> createState() =>
      _VirtualFittingScreenState();
}

class _VirtualFittingScreenState extends ConsumerState<VirtualFittingScreen> {
  static const int _maxVtonPayloadBytes = 7 * 1024 * 1024;

  // Current active product state (can be swapped via carousel)
  late int _productId;
  late String _productName;
  double? _price;

  // Camera capture preview. No live garment overlay is rendered over the feed.
  CameraController? _camera;
  CameraDescription? _cameraDescription;
  List<CameraDescription> _availableCameras = const [];
  int _cameraIndex = 0;
  bool _cameraAvailable = false;
  bool _cameraActive = false;
  bool _capturingPhoto = false;
  String? _cameraError;

  // Selected user photo awaiting confirmation. The catalog image is never used
  // as a body overlay or fake try-on input.
  Uint8List? _pendingPhotoBytes;
  String? _pendingPhotoBase64;
  String? _pendingPhotoSourceLabel;

  // Atelier VTON state
  bool _loadingVton = false;
  bool _loadingCatalog = false;
  bool _addingToCart = false;
  Map<String, dynamic>? _vtonResult;
  Uint8List? _compositeBytes;
  String? _vtonError;

  // Carousel garments
  List<CatalogItem> _availableGarments = [];

  @override
  void initState() {
    super.initState();
    _productId = widget.productId;
    _productName = widget.productName;
    _price = widget.price;

    _startFittingSession();
    _loadCatalogGarments();
    _checkCameraAvailable();
  }

  @override
  void dispose() {
    _camera?.dispose();
    super.dispose();
  }

  Future<void> _checkCameraAvailable() async {
    try {
      final cameras = await availableCameras();
      if (!mounted) return;
      if (cameras.isEmpty) {
        setState(() {
          _cameraAvailable = false;
          _cameraError = 'No encontramos una cámara en este dispositivo.';
        });
        return;
      }
      final preferredIndex = cameras.indexWhere(
        (item) => item.lensDirection == CameraLensDirection.front,
      );
      setState(() {
        _availableCameras = cameras;
        _cameraIndex = preferredIndex >= 0 ? preferredIndex : 0;
        _cameraAvailable = true;
        _cameraDescription = cameras[_cameraIndex];
        _cameraError = null;
      });
    } catch (_) {
      if (mounted) {
        setState(() {
          _cameraAvailable = false;
          _cameraError = 'No pudimos acceder a la cámara. Revisá los permisos.';
        });
      }
    }
  }

  Future<void> _toggleCameraMode() async {
    final messenger = ScaffoldMessenger.of(context);
    if (_cameraActive) {
      await _disposeCamera();
      return;
    }

    if (!_cameraAvailable || _cameraDescription == null) {
      messenger.showSnackBar(
        SnackBar(
          content: Text(
            _cameraError ??
                'Cámara no disponible. Continuamos en modo Estudio Atelier.',
          ),
        ),
      );
      return;
    }

    await _startSelectedCamera();
  }

  Future<void> _startSelectedCamera() async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      final controller = CameraController(
        _cameraDescription!,
        ResolutionPreset.low,
        enableAudio: false,
      );
      await controller.initialize();
      if (!mounted) {
        await controller.dispose();
        return;
      }
      setState(() {
        _camera = controller;
        _cameraActive = true;
        _cameraError = null;
      });
    } catch (_) {
      if (mounted) {
        setState(() {
          _cameraError =
              'No pudimos iniciar la cámara. Revisá permisos e intentá de nuevo.';
        });
        messenger.showSnackBar(SnackBar(content: Text(_cameraError!)));
      }
    }
  }

  Future<void> _switchCamera() async {
    if (_availableCameras.length < 2 || !_cameraActive) return;
    await _disposeCamera();
    if (!mounted) return;
    setState(() {
      _cameraIndex = (_cameraIndex + 1) % _availableCameras.length;
      _cameraDescription = _availableCameras[_cameraIndex];
    });
    await _startSelectedCamera();
  }

  String get _cameraLabel =>
      _cameraDescription?.lensDirection == CameraLensDirection.front
      ? 'Frontal'
      : 'Trasera';

  Future<void> _disposeCamera() async {
    final controller = _camera;
    _camera = null;
    if (mounted) {
      setState(() {
        _cameraActive = false;
        _capturingPhoto = false;
      });
    }
    await controller?.dispose();
  }

  Future<void> _chooseGalleryPhoto() async {
    try {
      final picker = widget.pickImageFromGallery;
      final file = picker != null
          ? await picker()
          : await ImagePicker().pickImage(source: ImageSource.gallery);
      if (!mounted || file == null) return;
      final bytes = await file.readAsBytes();
      if (!mounted) return;
      _preparePhotoForConfirmation(bytes, sourceLabel: 'galería');
    } catch (_) {
      if (!mounted) return;
      const message =
          'No pudimos leer la foto seleccionada. Elegí otra imagen e intentá de nuevo.';
      setState(() => _vtonError = message);
      _showTryOnError(message);
    }
  }

  Future<void> _capturePhotoForTryOn() async {
    final controller = _camera;
    if (controller == null || !controller.value.isInitialized) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Activá la cámara antes de capturar.'),
          action: SnackBarAction(
            label: 'ABRIR CÁMARA',
            onPressed: _toggleCameraMode,
          ),
        ),
      );
      return;
    }

    setState(() {
      _capturingPhoto = true;
      _cameraError = null;
      _vtonError = null;
      _pendingPhotoBytes = null;
      _pendingPhotoBase64 = null;
      _pendingPhotoSourceLabel = null;
    });

    try {
      final file = await controller.takePicture();
      final bytes = await file.readAsBytes();
      if (!mounted) return;
      _preparePhotoForConfirmation(bytes, sourceLabel: 'cámara');
      await _disposeCamera();
    } catch (_) {
      if (mounted) {
        setState(() {
          _cameraError =
              'No pudimos capturar la foto. Revisá permisos e intentá de nuevo.';
        });
        _showTryOnError(_cameraError!);
      }
    } finally {
      if (mounted) setState(() => _capturingPhoto = false);
    }
  }

  void _preparePhotoForConfirmation(
    Uint8List bytes, {
    required String sourceLabel,
  }) {
    final validationError = _validateUserPhoto(bytes);
    if (validationError != null) {
      setState(() {
        _pendingPhotoBytes = null;
        _pendingPhotoBase64 = null;
        _pendingPhotoSourceLabel = null;
        _vtonError = validationError;
        _vtonResult = null;
        _compositeBytes = null;
      });
      _showTryOnError(validationError);
      return;
    }

    setState(() {
      _pendingPhotoBytes = bytes;
      _pendingPhotoBase64 = base64Encode(bytes);
      _pendingPhotoSourceLabel = sourceLabel;
      _vtonError = null;
      _vtonResult = null;
      _compositeBytes = null;
    });
  }

  String? _validateUserPhoto(Uint8List bytes) {
    if (!_isSupportedPhoto(bytes)) {
      return 'Formato no soportado. Elegí una imagen JPG, PNG o WebP.';
    }
    final encodedPayloadBytes = base64Encode(bytes).length;
    if (encodedPayloadBytes > _maxVtonPayloadBytes) {
      return 'La foto supera el límite de 7 MB para subir. Elegí una imagen más liviana.';
    }
    return null;
  }

  bool _isSupportedPhoto(Uint8List bytes) {
    if (bytes.length < 12) return false;
    final isJpeg = bytes[0] == 0xFF && bytes[1] == 0xD8 && bytes[2] == 0xFF;
    final isPng =
        bytes[0] == 0x89 &&
        bytes[1] == 0x50 &&
        bytes[2] == 0x4E &&
        bytes[3] == 0x47 &&
        bytes[4] == 0x0D &&
        bytes[5] == 0x0A &&
        bytes[6] == 0x1A &&
        bytes[7] == 0x0A;
    final isWebP =
        bytes[0] == 0x52 &&
        bytes[1] == 0x49 &&
        bytes[2] == 0x46 &&
        bytes[3] == 0x46 &&
        bytes[8] == 0x57 &&
        bytes[9] == 0x45 &&
        bytes[10] == 0x42 &&
        bytes[11] == 0x50;
    return isJpeg || isPng || isWebP;
  }

  void _clearPendingPhoto() {
    setState(() {
      _pendingPhotoBytes = null;
      _pendingPhotoBase64 = null;
      _pendingPhotoSourceLabel = null;
      _vtonError = null;
    });
  }

  Future<void> _submitPendingPhoto() async {
    final photoB64 = _pendingPhotoBase64;
    if (photoB64 == null) return;
    await _loadVtonTryOn(userPhotoB64: photoB64);
  }

  Future<void> _startFittingSession() async {
    try {
      await ref
          .read(virtualFittingRepositoryProvider)
          .start(_productId, deviceInfo: 'mobile-look-atelier-vton');
    } catch (_) {}
  }

  Future<void> _loadCatalogGarments() async {
    setState(() => _loadingCatalog = true);
    try {
      final page = await ref.read(catalogRepositoryProvider).list();
      if (mounted) {
        setState(() {
          _availableGarments = page.items;
          _loadingCatalog = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loadingCatalog = false);
    }
  }

  Future<void> _loadVtonTryOn({required String userPhotoB64}) async {
    final source = _pendingPhotoSourceLabel == 'galería'
        ? 'gallery_photo'
        : 'camera_capture';
    setState(() {
      _loadingVton = true;
      _vtonError = null;
    });
    try {
      final result = await ref
          .read(virtualFittingRepositoryProvider)
          .vtonTryOn(
            _productId,
            imageBase64: userPhotoB64,
            metrics: {
              'torso_detected': true,
              'tilt_deg': 0.4,
              'device': source,
            },
          );

      Uint8List? bytes;
      final compositeStr = result['composite_image_base64'] as String?;
      if (compositeStr != null && compositeStr.isNotEmpty) {
        final raw = compositeStr.contains(',')
            ? compositeStr.split(',')[1]
            : compositeStr;
        bytes = base64Decode(raw);
      }

      if (mounted) {
        setState(() {
          _vtonResult = result;
          _compositeBytes = bytes;
          _pendingPhotoBytes = null;
          _pendingPhotoBase64 = null;
          _pendingPhotoSourceLabel = null;
          _loadingVton = false;
        });
      }
    } on ApiException catch (error) {
      if (mounted) {
        final message = error.statusCode == 502 || error.statusCode == 503
            ? 'Gemini no está disponible ahora. No mostraremos una simulación local ni una foto de catálogo.'
            : 'No pudimos generar la prueba virtual. Capturá otra foto con buena luz e intentá nuevamente.';
        setState(() {
          _loadingVton = false;
          _vtonError = message;
          _vtonResult = null;
          _compositeBytes = null;
        });
        _showTryOnError(message);
      }
    } catch (_) {
      if (mounted) {
        const message =
            'No pudimos generar la prueba virtual. Capturá otra foto con buena luz e intentá nuevamente.';
        setState(() {
          _loadingVton = false;
          _vtonError = message;
          _vtonResult = null;
          _compositeBytes = null;
        });
        _showTryOnError(message);
      }
    }
  }

  void _showTryOnError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        action: SnackBarAction(
          label: 'REINTENTAR',
          onPressed: _pendingPhotoBase64 == null
              ? _chooseGalleryPhoto
              : _submitPendingPhoto,
        ),
      ),
    );
  }

  void _selectGarment(CatalogItem item) {
    if (item.id == _productId) return;
    setState(() {
      _productId = item.id;
      _productName = item.name;
      _price = item.price;
      _vtonResult = null;
      _compositeBytes = null;
      _vtonError = null;
      _pendingPhotoBytes = null;
      _pendingPhotoBase64 = null;
      _pendingPhotoSourceLabel = null;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text(
          'Prenda seleccionada. Elegí o capturá una foto para generar la prueba virtual.',
        ),
        action: SnackBarAction(
          label: 'ELEGIR FOTO',
          onPressed: _chooseGalleryPhoto,
        ),
      ),
    );
  }

  Future<void> _addToCart() async {
    final messenger = ScaffoldMessenger.of(context);
    final nav = Navigator.of(context);
    setState(() => _addingToCart = true);
    try {
      final detail = await ref
          .read(catalogRepositoryProvider)
          .detail(_productId);
      if (detail.variants.isEmpty) {
        throw StateError('No hay variantes disponibles para esta prenda');
      }
      final variantId = detail.variants.first.id;
      await ref.read(cartRepositoryProvider).add(variantId);

      messenger.showSnackBar(
        SnackBar(
          backgroundColor: AppColors.charcoal,
          content: Row(
            children: [
              const Icon(Icons.check_circle, color: AppColors.gold),
              const SizedBox(width: AppSpacing.sm),
              Expanded(
                child: Text(
                  '¡$_productName añadida a tu bolsa de compras!',
                  style: const TextStyle(color: Colors.white),
                ),
              ),
            ],
          ),
          action: SnackBarAction(
            label: 'VER BOLSA',
            textColor: AppColors.gold,
            onPressed: () {
              nav.push(MaterialPageRoute(builder: (_) => const CartScreen()));
            },
          ),
        ),
      );
    } catch (e) {
      messenger.showSnackBar(
        SnackBar(content: Text('No pudimos añadir la prenda a la bolsa: $e')),
      );
    } finally {
      if (mounted) setState(() => _addingToCart = false);
    }
  }

  Future<void> _openReservationModal() async {
    List<Map<String, dynamic>> branches = [];
    try {
      branches = await ref.read(catalogRepositoryProvider).getBranches();
    } catch (_) {}

    if (!mounted) return;

    final parentMessenger = ScaffoldMessenger.of(context);
    final parentNav = Navigator.of(context);

    int? selectedBranchId = branches.isNotEmpty
        ? branches.first['id'] as int?
        : null;
    DateTime selectedDate = DateTime.now().add(const Duration(days: 1));
    bool reserving = false;

    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.ivoryDeep,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(AppRadii.xl)),
      ),
      builder: (ctx) => StatefulBuilder(
        builder: (modalContext, setModalState) => SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    const Icon(
                      Icons.storefront_outlined,
                      color: AppColors.goldDeep,
                      size: 28,
                    ),
                    const SizedBox(width: AppSpacing.sm),
                    Text(
                      'RESERVAR PROBADOR',
                      style: Theme.of(modalContext).textTheme.titleMedium
                          ?.copyWith(
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1.2,
                          ),
                    ),
                    const Spacer(),
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () => Navigator.pop(ctx),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.sm),
                Text(
                  'Ten lista la prenda "$_productName" en el probador de la sucursal de tu elección.',
                  style: Theme.of(modalContext).textTheme.bodyMedium,
                ),
                const SizedBox(height: AppSpacing.md),
                if (branches.isNotEmpty) ...[
                  Text(
                    'Seleccionar Sucursal:',
                    style: Theme.of(modalContext).textTheme.labelMedium
                        ?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  DropdownButtonFormField<int>(
                    initialValue: selectedBranchId,
                    decoration: const InputDecoration(
                      border: OutlineInputBorder(),
                      contentPadding: EdgeInsets.symmetric(
                        horizontal: AppSpacing.md,
                        vertical: AppSpacing.sm,
                      ),
                    ),
                    items: branches.map((b) {
                      return DropdownMenuItem<int>(
                        value: b['id'] as int,
                        child: Text('${b['name']} (${b['city'] ?? ''})'),
                      );
                    }).toList(),
                    onChanged: (val) {
                      if (val != null) {
                        setModalState(() => selectedBranchId = val);
                      }
                    },
                  ),
                  const SizedBox(height: AppSpacing.md),
                ],
                Text(
                  'Fecha de Visita:',
                  style: Theme.of(modalContext).textTheme.labelMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: AppSpacing.xs),
                OutlinedButton.icon(
                  icon: const Icon(Icons.calendar_today_outlined),
                  label: Text(
                    '${selectedDate.day}/${selectedDate.month}/${selectedDate.year}',
                  ),
                  onPressed: () async {
                    final picked = await showDatePicker(
                      context: modalContext,
                      initialDate: selectedDate,
                      firstDate: DateTime.now(),
                      lastDate: DateTime.now().add(const Duration(days: 60)),
                    );
                    if (picked != null) {
                      setModalState(() => selectedDate = picked);
                    }
                  },
                ),
                const SizedBox(height: AppSpacing.lg),
                FilledButton.icon(
                  onPressed: reserving
                      ? null
                      : () async {
                          setModalState(() => reserving = true);
                          try {
                            final detail = await ref
                                .read(catalogRepositoryProvider)
                                .detail(_productId);
                            if (detail.variants.isEmpty) {
                              throw StateError(
                                'No hay variantes de esta prenda para reservar',
                              );
                            }
                            final variantId = detail.variants.first.id;
                            final branchId = selectedBranchId ?? 1;

                            await ref
                                .read(reservationRepositoryProvider)
                                .create(
                                  branchId: branchId,
                                  scheduledFor: selectedDate,
                                  items: [
                                    {
                                      'product_variant_id': variantId,
                                      'quantity': 1,
                                    },
                                  ],
                                );

                            if (!ctx.mounted) return;
                            Navigator.pop(ctx);
                            parentMessenger.showSnackBar(
                              SnackBar(
                                backgroundColor: AppColors.charcoal,
                                content: const Text(
                                  '¡Turno de probador reservado con éxito!',
                                  style: TextStyle(color: Colors.white),
                                ),
                                action: SnackBarAction(
                                  label: 'VER MIS RESERVAS',
                                  textColor: AppColors.gold,
                                  onPressed: () {
                                    parentNav.push(
                                      MaterialPageRoute(
                                        builder: (_) =>
                                            const ReservationsScreen(),
                                      ),
                                    );
                                  },
                                ),
                              ),
                            );
                          } catch (err) {
                            setModalState(() => reserving = false);
                            parentMessenger.showSnackBar(
                              SnackBar(
                                content: Text(
                                  'No se pudo completar la reserva: $err',
                                ),
                              ),
                            );
                          }
                        },
                  icon: reserving
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.check),
                  label: Text(
                    reserving
                        ? 'Procesando...'
                        : 'Confirmar Reserva de Probador',
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final calcePorcentaje = (_vtonResult?['calce_porcentaje'] as num?)
        ?.toDouble();
    final veredicto = _vtonResult?['veredicto_estilista'] as String?;
    final tallaSugerida = _vtonResult?['talla_sugerida'] as String?;
    final providerStatus =
        (_vtonResult?['provider_status'] ?? _vtonResult?['status']) as String?;

    return Scaffold(
      backgroundColor: AppColors.ivoryDeep,
      appBar: AppBar(
        title: Column(
          children: [
            Text(
              'LOOK ATELIER',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
                letterSpacing: 2.0,
              ),
            ),
            const Text(
              'GEMINI • PROBADOR VIRTUAL',
              style: TextStyle(
                fontSize: 10,
                letterSpacing: 1.2,
                color: AppColors.goldDeep,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: AppSpacing.sm),
            child: ActionChip(
              avatar: Icon(
                _cameraActive
                    ? Icons.auto_awesome_mosaic_outlined
                    : Icons.camera_alt_outlined,
                size: 16,
                color: AppColors.charcoal,
              ),
              label: Text(
                _cameraActive ? 'Estudio' : 'Capturar',
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                ),
              ),
              backgroundColor: AppColors.ivory,
              onPressed: _toggleCameraMode,
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.md),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _buildHeaderBadge(),
                const SizedBox(height: AppSpacing.sm),
                _buildFittingViewport(),
                const SizedBox(height: AppSpacing.sm),
                _buildStylistCard(
                  calcePorcentaje,
                  tallaSugerida,
                  veredicto,
                  providerStatus,
                ),
                const SizedBox(height: AppSpacing.md),
                _buildGarmentCarousel(),
                const SizedBox(height: AppSpacing.md),
                _buildActionButtons(),
                const SizedBox(height: AppSpacing.sm),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeaderBadge() {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.md,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        color: AppColors.charcoal,
        borderRadius: BorderRadius.circular(100),
        border: Border.all(color: AppColors.goldDeep.withValues(alpha: 0.5)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.auto_awesome, color: AppColors.gold, size: 14),
          const SizedBox(width: AppSpacing.xs),
          const Text(
            'LOOK ATELIER • GEMINI AI',
            style: TextStyle(
              color: AppColors.gold,
              fontSize: 12,
              fontWeight: FontWeight.bold,
              letterSpacing: 1.5,
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Container(
            width: 6,
            height: 6,
            decoration: const BoxDecoration(
              color: Colors.greenAccent,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 4),
          Text(
            _cameraActive ? 'PREVIEW CÁMARA' : 'ESTUDIO HD',
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 10,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFittingViewport() {
    return Container(
      height: 380,
      decoration: BoxDecoration(
        color: const Color(0xFF141416),
        borderRadius: BorderRadius.circular(AppRadii.xl),
        border: Border.all(
          color: AppColors.goldDeep.withValues(alpha: 0.4),
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.25),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(AppRadii.xl),
        child: Stack(
          fit: StackFit.expand,
          children: [
            if (_cameraActive &&
                _camera != null &&
                _camera!.value.isInitialized)
              _buildCameraStream()
            else if (_pendingPhotoBytes != null)
              _buildPendingPhotoPreview()
            else
              _buildStudioRender(),

            Positioned(
              top: AppSpacing.sm,
              right: AppSpacing.sm,
              child: _buildGeminiHudBadge(),
            ),

            Positioned(
              top: AppSpacing.sm,
              left: AppSpacing.sm,
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.sm,
                  vertical: 4,
                ),
                decoration: BoxDecoration(
                  color: Colors.black54,
                  borderRadius: BorderRadius.circular(AppRadii.sm),
                  border: Border.all(color: Colors.white24),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      _cameraActive ? Icons.videocam : Icons.checkroom,
                      color: AppColors.gold,
                      size: 12,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      _cameraActive
                          ? 'PREVIEW PARA CAPTURA'
                          : _pendingPhotoBytes != null
                          ? 'CONFIRMAR FOTO'
                          : 'ESTUDIO NEUTRAL',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 10,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            if (_cameraActive && _availableCameras.length > 1)
              Positioned(
                top: 62,
                right: AppSpacing.sm,
                child: Material(
                  color: Colors.black54,
                  borderRadius: BorderRadius.circular(AppRadii.sm),
                  child: InkWell(
                    onTap: _switchCamera,
                    borderRadius: BorderRadius.circular(AppRadii.sm),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 7,
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(
                            Icons.flip_camera_ios_outlined,
                            color: Colors.white,
                            size: 17,
                          ),
                          const SizedBox(width: 5),
                          Text(
                            _cameraLabel,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 10,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),

            if (_loadingVton)
              Container(
                color: Colors.black45,
                child: const Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      CircularProgressIndicator(color: AppColors.gold),
                      SizedBox(height: AppSpacing.sm),
                      Text(
                        'Generando prueba virtual desde tu foto...',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildGeminiHudBadge() {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: 6,
      ),
      decoration: BoxDecoration(
        color: const Color(0xDD121214),
        borderRadius: BorderRadius.circular(AppRadii.md),
        border: Border.all(color: AppColors.gold, width: 1.2),
        boxShadow: [
          BoxShadow(
            color: AppColors.gold.withValues(alpha: 0.2),
            blurRadius: 8,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.end,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 7,
                height: 7,
                decoration: BoxDecoration(
                  color: Colors.greenAccent,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 5),
              Text(
                'RESULTADO GEMINI',
                style: const TextStyle(
                  color: AppColors.gold,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.8,
                ),
              ),
            ],
          ),
          const SizedBox(height: 2),
          Text(
            'Foto + prenda procesadas por Gemini',
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 9,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPendingPhotoPreview() {
    return Stack(
      fit: StackFit.expand,
      children: [
        Container(color: const Color(0xFF141416)),
        Image.memory(_pendingPhotoBytes!, fit: BoxFit.contain),
        Positioned(
          left: AppSpacing.md,
          right: AppSpacing.md,
          bottom: AppSpacing.md,
          child: Container(
            padding: const EdgeInsets.all(AppSpacing.sm),
            decoration: BoxDecoration(
              color: Colors.black.withValues(alpha: 0.72),
              borderRadius: BorderRadius.circular(AppRadii.md),
              border: Border.all(color: Colors.white24),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  'Foto de ${_pendingPhotoSourceLabel ?? "usuario"} lista. Confirmá para enviarla a Gemini.',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.white, fontSize: 12),
                ),
                const SizedBox(height: AppSpacing.sm),
                FilledButton.icon(
                  onPressed: _loadingVton ? null : _submitPendingPhoto,
                  icon: const Icon(Icons.auto_awesome),
                  label: const Text('Generar prueba virtual'),
                ),
                const SizedBox(height: AppSpacing.xs),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: _loadingVton ? null : _chooseGalleryPhoto,
                        icon: const Icon(Icons.photo_library_outlined),
                        label: const Text('Elegir otra'),
                      ),
                    ),
                    const SizedBox(width: AppSpacing.xs),
                    Expanded(
                      child: TextButton.icon(
                        onPressed: _loadingVton ? null : _clearPendingPhoto,
                        icon: const Icon(Icons.close),
                        label: const Text('Cancelar'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildStudioRender() {
    if (_compositeBytes != null) {
      return Image.memory(
        _compositeBytes!,
        fit: BoxFit.contain,
        errorBuilder: (context, error, stackTrace) => _buildFallbackMannequin(),
      );
    }
    return _buildFallbackMannequin();
  }

  Widget _buildFallbackMannequin() {
    return Stack(
      alignment: Alignment.center,
      children: [
        Container(
          decoration: const BoxDecoration(
            gradient: RadialGradient(
              center: Alignment(0, -0.4),
              radius: 0.9,
              colors: [Color(0xFF2C251F), Color(0xFF141416)],
            ),
          ),
        ),
        CustomPaint(size: const Size(260, 360), painter: _MannequinPainter()),
        Positioned(
          left: AppSpacing.lg,
          right: AppSpacing.lg,
          bottom: AppSpacing.lg,
          child: _buildStudioPrompt(),
        ),
      ],
    );
  }

  Widget _buildCameraStream() {
    final camera = _camera!;
    return Stack(
      fit: StackFit.expand,
      children: [
        CameraPreview(camera),
        Container(
          decoration: BoxDecoration(
            border: Border.all(color: AppColors.gold.withValues(alpha: 0.5)),
          ),
        ),
        Positioned(
          left: AppSpacing.md,
          right: AppSpacing.md,
          bottom: AppSpacing.md,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const StatusPill(
                label: 'Vista previa: capturá una foto para enviarla a Gemini',
              ),
              if (_cameraError != null) ...[
                const SizedBox(height: AppSpacing.xs),
                Text(
                  _cameraError!,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.white, fontSize: 12),
                ),
              ],
              const SizedBox(height: AppSpacing.sm),
              FilledButton.icon(
                onPressed: _capturingPhoto || _loadingVton
                    ? null
                    : _capturePhotoForTryOn,
                icon: _capturingPhoto
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.camera_alt_outlined),
                label: Text(
                  _capturingPhoto ? 'Capturando...' : 'Capturar foto',
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildStudioPrompt() {
    final message =
        _vtonError ??
        'Estudio neutral listo. Elegí una foto de galería o capturá una nueva para generar la prueba virtual de $_productName.';
    return Container(
      padding: const EdgeInsets.all(AppSpacing.sm),
      decoration: BoxDecoration(
        color: Colors.black54,
        borderRadius: BorderRadius.circular(AppRadii.md),
        border: Border.all(color: Colors.white24),
      ),
      child: Row(
        children: [
          Icon(
            _vtonError == null
                ? Icons.camera_alt_outlined
                : Icons.error_outline,
            color: AppColors.gold,
            size: 18,
          ),
          const SizedBox(width: AppSpacing.xs),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(color: Colors.white, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStylistCard(
    double? calcePorcentaje,
    String? tallaSugerida,
    String? veredicto,
    String? providerStatus,
  ) {
    return Card(
      elevation: 0,
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppRadii.lg),
        side: const BorderSide(color: AppColors.ivoryDeep),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    _productName,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                if (_price != null)
                  Text(
                    'Bs. ${_price!.toStringAsFixed(2)}',
                    style: const TextStyle(
                      color: AppColors.goldDeep,
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                    ),
                  ),
              ],
            ),
            const SizedBox(height: AppSpacing.xs),
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.sm,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.ivoryDeep,
                    borderRadius: BorderRadius.circular(AppRadii.sm),
                  ),
                  child: Text(
                    tallaSugerida == null
                        ? 'TALLA SUGERIDA: PENDIENTE'
                        : 'TALLA SUGERIDA: $tallaSugerida',
                    style: const TextStyle(
                      color: AppColors.charcoal,
                      fontWeight: FontWeight.bold,
                      fontSize: 11,
                    ),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.sm,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.green.shade50,
                    borderRadius: BorderRadius.circular(AppRadii.sm),
                  ),
                  child: Text(
                    'RESULTADO: GEMINI',
                    style: TextStyle(
                      color: Colors.green.shade800,
                      fontWeight: FontWeight.bold,
                      fontSize: 11,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.sm),
            if (_compositeBytes != null) ...[
              Row(
                children: [
                  const Icon(
                    Icons.verified_outlined,
                    color: AppColors.goldDeep,
                    size: 16,
                  ),
                  const SizedBox(width: AppSpacing.xs),
                  Expanded(
                    child: Text(
                      'Gemini: ${providerStatus ?? "completado"}',
                      style: const TextStyle(
                        color: AppColors.charcoalMuted,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.sm),
            ],
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.auto_awesome, color: AppColors.gold, size: 16),
                const SizedBox(width: AppSpacing.xs),
                Expanded(
                  child: Text(
                    veredicto ??
                        'Elegí o capturá una foto para que Gemini coloque la prenda seleccionada.',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: AppColors.charcoalMuted,
                      height: 1.3,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildGarmentCarousel() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(
              Icons.checkroom_outlined,
              color: AppColors.gold,
              size: 18,
            ),
            const SizedBox(width: AppSpacing.xs),
            Text(
              'PROBAR OTRA PRENDA',
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                fontWeight: FontWeight.bold,
                letterSpacing: 1.2,
              ),
            ),
            const Spacer(),
            if (_availableGarments.isNotEmpty)
              Text(
                '${_availableGarments.length} disponibles',
                style: const TextStyle(
                  color: AppColors.charcoalMuted,
                  fontSize: 11,
                  fontWeight: FontWeight.w500,
                ),
              ),
          ],
        ),
        const SizedBox(height: AppSpacing.xs),
        SizedBox(
          height: 124,
          child: _loadingCatalog
              ? const Center(
                  child: CircularProgressIndicator(color: AppColors.gold),
                )
              : _availableGarments.isEmpty
              ? const Center(child: Text('No hay otras prendas disponibles.'))
              : ListView.builder(
                  scrollDirection: Axis.horizontal,
                  itemCount: _availableGarments.length,
                  itemBuilder: (context, index) {
                    final item = _availableGarments[index];
                    final isSelected = item.id == _productId;
                    return GestureDetector(
                      onTap: () => _selectGarment(item),
                      child: Container(
                        width: 90,
                        margin: const EdgeInsets.only(right: AppSpacing.sm),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(AppRadii.md),
                          border: Border.all(
                            color: isSelected
                                ? AppColors.gold
                                : AppColors.ivoryDeep,
                            width: isSelected ? 2.0 : 1.0,
                          ),
                          boxShadow: isSelected
                              ? [
                                  BoxShadow(
                                    color: AppColors.gold.withValues(
                                      alpha: 0.3,
                                    ),
                                    blurRadius: 6,
                                    offset: const Offset(0, 2),
                                  ),
                                ]
                              : null,
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(6.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Expanded(
                                child: Stack(
                                  fit: StackFit.expand,
                                  children: [
                                    ClipRRect(
                                      borderRadius: BorderRadius.circular(
                                        AppRadii.sm,
                                      ),
                                      child:
                                          item.imageUrl != null &&
                                              item.imageUrl!.isNotEmpty
                                          ? Image.network(
                                              item.imageUrl!,
                                              fit: BoxFit.cover,
                                              errorBuilder:
                                                  (
                                                    context,
                                                    error,
                                                    stackTrace,
                                                  ) => const Center(
                                                    child: Icon(
                                                      Icons.checkroom,
                                                      size: 32,
                                                      color: Colors.grey,
                                                    ),
                                                  ),
                                            )
                                          : const Center(
                                              child: Icon(
                                                Icons.checkroom,
                                                size: 32,
                                                color: Colors.grey,
                                              ),
                                            ),
                                    ),
                                    if (isSelected)
                                      Positioned(
                                        top: 2,
                                        left: 2,
                                        child: Container(
                                          padding: const EdgeInsets.symmetric(
                                            horizontal: 4,
                                            vertical: 1,
                                          ),
                                          decoration: BoxDecoration(
                                            color: AppColors.gold,
                                            borderRadius: BorderRadius.circular(
                                              3,
                                            ),
                                          ),
                                          child: const Text(
                                            'ACTIVA',
                                            style: TextStyle(
                                              color: Colors.white,
                                              fontSize: 8,
                                              fontWeight: FontWeight.bold,
                                            ),
                                          ),
                                        ),
                                      ),
                                  ],
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                item.name,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: isSelected
                                      ? FontWeight.bold
                                      : FontWeight.normal,
                                ),
                              ),
                              Text(
                                'Bs. ${item.price.toStringAsFixed(0)}',
                                style: const TextStyle(
                                  fontSize: 10,
                                  color: AppColors.goldDeep,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }

  Widget _buildActionButtons() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        FilledButton.icon(
          style: FilledButton.styleFrom(
            backgroundColor: AppColors.goldDeep,
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppRadii.md),
            ),
          ),
          onPressed: _loadingVton ? null : _chooseGalleryPhoto,
          icon: const Icon(Icons.photo_library_outlined),
          label: const Text(
            'ELEGIR FOTO DE GALERÍA',
            style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 0.5),
          ),
        ),
        const SizedBox(height: AppSpacing.sm),
        OutlinedButton.icon(
          style: OutlinedButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
            side: const BorderSide(color: AppColors.gold, width: 1.5),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppRadii.md),
            ),
          ),
          onPressed: _loadingVton ? null : _toggleCameraMode,
          icon: Icon(
            _cameraActive ? Icons.close : Icons.camera_alt_outlined,
            color: AppColors.gold,
          ),
          label: Text(
            _cameraActive ? 'CERRAR CÁMARA' : 'USAR CÁMARA',
            style: const TextStyle(
              color: AppColors.charcoal,
              fontWeight: FontWeight.bold,
              letterSpacing: 0.5,
            ),
          ),
        ),
        if (_compositeBytes != null || _vtonError != null) ...[
          const SizedBox(height: AppSpacing.sm),
          TextButton.icon(
            onPressed: _loadingVton
                ? null
                : (_pendingPhotoBase64 == null
                      ? _chooseGalleryPhoto
                      : _submitPendingPhoto),
            icon: Icon(
              _vtonError == null ? Icons.refresh : Icons.replay_outlined,
            ),
            label: Text(
              _vtonError == null ? 'Probar con otra foto' : 'Reintentar',
            ),
          ),
        ],
        const SizedBox(height: AppSpacing.xs),
        const Text(
          'Guardar o compartir el resultado no se agrega en esta versión para evitar dependencias móviles extra; podés reintentar, cambiar prenda o añadir a bolsa.',
          textAlign: TextAlign.center,
          style: TextStyle(color: AppColors.charcoalMuted, fontSize: 11),
        ),
        const SizedBox(height: AppSpacing.sm),
        Row(
          children: [
            // "RESERVAR PROBADOR" (CU10)
            Expanded(
              child: OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
                  side: const BorderSide(color: AppColors.gold, width: 1.5),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(AppRadii.md),
                  ),
                ),
                onPressed: _openReservationModal,
                icon: const Icon(
                  Icons.event_available_outlined,
                  color: AppColors.gold,
                  size: 20,
                ),
                label: const Text(
                  'RESERVAR PROBADOR',
                  style: TextStyle(
                    color: AppColors.charcoal,
                    fontWeight: FontWeight.bold,
                    fontSize: 11,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
            ),
            const SizedBox(width: AppSpacing.sm),

            // "AÑADIR A BOLSA" (CU13)
            Expanded(
              child: FilledButton.icon(
                style: FilledButton.styleFrom(
                  backgroundColor: AppColors.charcoal,
                  padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(AppRadii.md),
                  ),
                ),
                onPressed: _addingToCart ? null : _addToCart,
                icon: _addingToCart
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: AppColors.gold,
                        ),
                      )
                    : const Icon(
                        Icons.shopping_bag_outlined,
                        color: AppColors.gold,
                        size: 20,
                      ),
                label: Text(
                  _addingToCart ? 'AÑADIENDO...' : 'AÑADIR A BOLSA',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 11,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }
}

/// Custom painter to render a neutral studio mannequin bust.
class _MannequinPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final strokePaint = Paint()
      ..color = const Color(0x66C5A880)
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;

    final fillPaint = Paint()
      ..color = const Color(0xFF1E1E22)
      ..style = PaintingStyle.fill;

    final cx = size.width / 2;

    // Mannequin neck
    final neckRect = Rect.fromCenter(
      center: Offset(cx, 60),
      width: 44,
      height: 24,
    );
    canvas.drawOval(neckRect, fillPaint);
    canvas.drawOval(neckRect, strokePaint);

    // Torso path
    final path = Path();
    path.moveTo(cx - 22, 65);
    path.lineTo(cx - 95, 110);
    path.lineTo(cx - 80, 240);
    path.lineTo(cx - 60, 310);
    path.lineTo(cx + 60, 310);
    path.lineTo(cx + 80, 240);
    path.lineTo(cx + 95, 110);
    path.lineTo(cx + 22, 65);
    path.close();

    canvas.drawPath(path, fillPaint);
    canvas.drawPath(path, strokePaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
