<template>
  <router-link :to="`/groups/${groupName}`" class="navbar-item">{{ groupDescription }}</router-link>
</template>

<script>
export default {
  name: 'GroupButton',
  props: {

    groupName: String,
    groupDescription: String,
  },
};
</script>
