from django.contrib import admin

from stream.models import VideoStream, Chunk
# Register your models here.
admin.site.register(Chunk)

class ChunkInline(admin.TabularInline):  # or StackedInline
    model = Chunk
    extra = 0  # don't show empty rows
    readonly_fields = ('id',)  # optional

@admin.register(VideoStream)
class VideoStreamAdmin(admin.ModelAdmin):
    list_display = ('id', 'started',)
    readonly_fields = ('started',)
    inlines = [ChunkInline]