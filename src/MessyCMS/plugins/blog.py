from MessyCMS import plugins
from MessyCMS.models import Node

## Items list with cursor type pagination (like on Reddit)

class ItemslistCursorPaginated(plugins.ItemsList):
    def execute(self, node, request=None, *args, **kwargs):
        result = result = {
            'templates': plugins.templates(node, request),
            'context': {
                'nodes': None,
                'node': node,
                'next_page': None,
                'prev_page': None,
                'last_page': None,
            }
        }
        
        if node.link:
            items = node.link.get_children().filter(available=True)
        else:
            ## Using parent if no link defined
            items = node.parent.parent.get_children().filter(available=True)
        
        items = items.order_by('-timestamp', '-id')
        limit = int(node.prop('limit', 10))
        
        if limit:
            try:
                node_id = int(request.GET.get('page', 0))
            except:
                node_id = 0
            
            sliced = items
            
            current_node = Node.objects.filter(id=node_id).first()
            if current_node:
                sliced = sliced.filter(timestamp__lte=current_node.timestamp)
            
            sliced = sliced[:limit + 1]
            result['context']['nodes'] = sliced[:limit]
            
            ## There is next page
            if sliced.count() > limit:
                ## Getting first item of next page.
                ## It's not possible to use .last(), it fails with error
                ## "Cannot reverse a query once a slice has been taken".
                result['context']['next_page'] = sliced[limit]
                
                ## Get last page
                result['context']['last_page'] = items[items.count() - limit:][0]
            
            ## Checkout if there is prev page
            if current_node:
                sliced = items.filter(timestamp__gt=current_node.timestamp)
                if sliced:
                    result['context']['prev_page'] = sliced[sliced.count() - limit:][0]
        
        node.context.update(result['context'])
        return result
