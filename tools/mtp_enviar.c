// mtp_enviar — copia un .prg a GARMIN/Apps del reloj por MTP (libmtp).
//
//   mtp_enviar <local.prg> <NOMBRE.PRG>
//
// mtp-sendfile de libmtp no resuelve bien la carpeta destino en el Fenix 7X Pro
// (PID 0x5118, desconocido para libmtp 1.1.23): aquí se busca GARMIN/Apps por
// nombre en el árbol de carpetas y se envía con su id y su almacenamiento.
// Si ya existe un fichero con ese nombre en Apps (una versión anterior de la
// esfera), se sustituye.
//
// Compilar: clang -O2 -o mtp_enviar mtp_enviar.c -I/opt/homebrew/include -L/opt/homebrew/lib -lmtp
#include <libmtp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <sys/stat.h>

static LIBMTP_folder_t *hijo(LIBMTP_folder_t *f, const char *nombre) {
    for (; f; f = f->sibling)
        if (f->name && strcasecmp(f->name, nombre) == 0) return f;
    return NULL;
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "uso: %s <local.prg> <NOMBRE.PRG>\n", argv[0]);
        return 2;
    }
    struct stat st;
    if (stat(argv[1], &st) != 0) { perror(argv[1]); return 2; }

    LIBMTP_Init();
    LIBMTP_mtpdevice_t *dev = LIBMTP_Get_First_Device();
    if (!dev) { fprintf(stderr, "No hay reloj MTP conectado.\n"); return 1; }

    LIBMTP_folder_t *raiz = LIBMTP_Get_Folder_List(dev);
    LIBMTP_folder_t *garmin = hijo(raiz, "GARMIN");
    LIBMTP_folder_t *apps = garmin ? hijo(garmin->child, "Apps") : NULL;
    if (!apps) { fprintf(stderr, "No encuentro GARMIN/Apps.\n"); return 1; }
    printf("GARMIN/Apps: id %u, almacenamiento 0x%08x\n", apps->folder_id, apps->storage_id);

    // Sustituir una versión anterior con el mismo nombre.
    // El dispositivo se abre en modo caché: el listado es global y se filtra por carpeta.
    LIBMTP_file_t *lista = LIBMTP_Get_Filelisting_With_Callback(dev, NULL, NULL);
    for (LIBMTP_file_t *f = lista; f; f = f->next) {
        if (f->parent_id == apps->folder_id && f->filename && strcasecmp(f->filename, argv[2]) == 0) {
            printf("Sustituyendo %s (id %u, %llu bytes)\n", f->filename, f->item_id,
                   (unsigned long long)f->filesize);
            if (LIBMTP_Delete_Object(dev, f->item_id) != 0) {
                LIBMTP_Dump_Errorstack(dev);
                return 1;
            }
        }
    }

    LIBMTP_file_t *nuevo = LIBMTP_new_file_t();
    nuevo->filename = strdup(argv[2]);
    nuevo->filesize = st.st_size;
    nuevo->filetype = LIBMTP_FILETYPE_UNKNOWN;
    nuevo->parent_id = apps->folder_id;
    nuevo->storage_id = apps->storage_id;
    int r = LIBMTP_Send_File_From_File(dev, argv[1], nuevo, NULL, NULL);
    if (r != 0) {
        LIBMTP_Dump_Errorstack(dev);
        fprintf(stderr, "Fallo al enviar.\n");
        return 1;
    }
    printf("Enviado %s → GARMIN/Apps/%s (id %u, %lld bytes)\n", argv[1], argv[2], nuevo->item_id,
           (long long)st.st_size);
    LIBMTP_Release_Device(dev);
    return 0;
}
