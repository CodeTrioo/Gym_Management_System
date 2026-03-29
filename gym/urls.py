from django.urls import path
from gym import views

urlpatterns = [
    # Public
    path('', views.overview, name='overview'),

    # Member Portal
    path('portal/member/', views.member_portal, name='member_portal'),
    path('portal/member/choose-trainer/', views.select_trainer_view, name='select_trainer_view'),
    path('portal/member/select-trainer/', views.process_trainer_selection, name='process_trainer_selection'),
    path('portal/member/log-progress/', views.log_progress, name='log_progress'),
    path('portal/member/slots/', views.get_instructor_slots, name='instructor_slots'),
    path('portal/member/book/<int:slot_id>/', views.book_slot, name='book_slot'),
    path('portal/member/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('portal/member/exercise/toggle/<int:exercise_id>/', views.toggle_exercise_completion, name='toggle_exercise_completion'),
    path('portal/member/meal/toggle/<int:meal_id>/', views.toggle_meal_completion, name='toggle_meal_completion'),
    path('portal/member/nutrient-proxy/', views.nutrient_proxy, name='nutrient_proxy'),

    # Staff Portal
    path('portal/staff/', views.staff_portal, name='staff_portal'),
    path('portal/staff/slots/', views.get_staff_slots, name='staff_slots'),
    path('portal/staff/slots/add/', views.add_slot, name='add_slot'),
    path('portal/staff/slots/delete/<int:slot_id>/', views.delete_slot, name='delete_slot'),

    path('portal/staff/diet/<int:member_id>/', views.save_diet_plan, name='save_diet_plan'),
    path('portal/staff/remove-plan/<int:member_id>/', views.remove_member_plan, name='remove_member_plan'),
    path('portal/staff/meal/<int:plan_id>/', views.save_meal, name='save_meal'),
    path('portal/staff/meal/delete/<int:meal_id>/', views.delete_meal, name='delete_meal'),
    path('portal/staff/workout/<int:member_id>/', views.save_workout_plan, name='save_workout_plan'),
    path('portal/staff/member-data/<int:member_id>/', views.get_member_data, name='get_member_data'),
    path('portal/staff/exercise/<int:plan_id>/', views.save_exercise, name='save_exercise'),
    path('portal/staff/exercise/delete/<int:exercise_id>/', views.delete_exercise, name='delete_exercise'),
    path('portal/staff/global-workout/', views.save_global_workout, name='save_global_workout'),
    path('portal/staff/global-workout/delete/<int:workout_id>/', views.delete_global_workout, name='delete_global_workout'),
    path('portal/staff/assign-plan/<int:plan_id>/', views.assign_plan, name='assign_plan'),
    path('portal/staff/duplicate-plan/<int:plan_id>/', views.duplicate_plan, name='duplicate_plan'),
    path('portal/staff/plan-detail/<int:plan_id>/', views.get_plan_detail, name='get_plan_detail'),
    path('portal/staff/delete-template/<int:plan_id>/', views.delete_template, name='delete_template'),
    path('portal/staff/copy-day/<int:plan_id>/', views.copy_day, name='copy_day'),
    path('portal/staff/feedback/<int:member_id>/', views.save_feedback, name='save_feedback'),

    # Admin Portal
    path('portal/admin/', views.admin_portal, name='admin_portal'),
    path('portal/admin/access/<int:staff_id>/', views.manage_access, name='manage_access'),
    path('portal/admin/assign-instructor/', views.assign_instructor, name='assign_instructor'),
    path('portal/admin/announcement/', views.save_announcement, name='save_announcement'),
    path('portal/admin/plan/', views.save_plan, name='save_plan'),
    path('portal/admin/member/delete/<int:user_id>/', views.delete_member, name='delete_member'),
    path('portal/admin/staff/delete/<int:user_id>/', views.delete_staff, name='delete_staff'),
    path('portal/admin/plan/delete/<int:plan_id>/', views.delete_plan, name='delete_plan'),
    path('portal/admin/announcement/delete/<int:ann_id>/', views.delete_announcement, name='delete_announcement'),
    path('portal/admin/gallery/', views.save_gallery_image, name='save_gallery_image'),
    path('portal/admin/gallery/delete/<int:img_id>/', views.delete_gallery_image, name='delete_gallery_image'),
]
